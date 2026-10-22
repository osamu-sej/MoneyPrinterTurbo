"""Local revisions of completed videos. Originals and provider calls stay untouched."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class VideoEditError(ValueError):
    pass


@dataclass(frozen=True)
class MediaInfo:
    duration: float
    has_audio: bool


@dataclass(frozen=True)
class SubtitleCue:
    timing: str
    text: str


_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_FINAL = re.compile(r"^final-(\d+)\.mp4$")
_EDIT = re.compile(r"^edit-\d{8}-\d{6}-[a-f0-9]{8}\.mp4$")
_TIMING = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})$")


def task_directory(tasks_root: str | Path, task_id: str) -> Path:
    if not _TASK_ID.fullmatch(str(task_id)):
        raise VideoEditError("タスクIDが正しくありません。")
    root = Path(tasks_root).resolve()
    folder = (root / task_id).resolve()
    if folder.parent != root or not folder.is_dir():
        raise VideoEditError("動画の保存先が見つかりません。")
    return folder


def _inside_task(folder: Path, path: Path) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or not resolved.is_relative_to(folder.resolve()):
        raise VideoEditError("タスク外のファイルは編集できません。")
    return resolved


def original_videos(folder: Path) -> list[Path]:
    return sorted(
        (_inside_task(folder, path) for path in folder.glob("final-*.mp4") if _FINAL.fullmatch(path.name)),
        key=lambda path: int(_FINAL.fullmatch(path.name).group(1)),
    )


def edited_videos(folder: Path) -> list[Path]:
    edit_dir = folder / "edits"
    if not edit_dir.is_dir():
        return []
    return sorted(
        (_inside_task(folder, path) for path in edit_dir.glob("edit-*.mp4") if _EDIT.fullmatch(path.name)),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def allowed_source(folder: Path, path: str | Path) -> Path:
    folder = folder.resolve()
    candidate = _inside_task(folder, Path(path))
    if candidate.parent == folder and _FINAL.fullmatch(candidate.name):
        return candidate
    if candidate.parent == folder / "edits" and _EDIT.fullmatch(candidate.name):
        return candidate
    raise VideoEditError("完成動画か保存済みの編集版を選んでください。")


def probe_media(path: Path) -> MediaInfo:
    from moviepy import VideoFileClip

    try:
        with VideoFileClip(str(path), audio=False) as clip:
            duration = float(clip.duration)
            has_audio = bool(clip.reader.infos.get("audio_found"))
    except Exception as exc:
        raise VideoEditError("動画を読み取れません。ファイルを確認してください。") from exc
    if not math.isfinite(duration) or not 0.5 <= duration <= 3600:
        raise VideoEditError("編集できる動画は0.5秒以上、1時間以内です。")
    return MediaInfo(duration, has_audio)


def _timestamp_seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, milliseconds = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def read_subtitles(path: Path) -> list[SubtitleCue]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    if len(text) > 100_000:
        raise VideoEditError("字幕が長すぎるため、この画面では編集できません。")
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        if not block.strip():
            continue
        lines = block.splitlines()
        if lines[0].strip().isdigit():
            lines = lines[1:]
        if len(lines) < 2:
            raise VideoEditError("字幕ファイルの形式を読み取れません。")
        timing = lines[0].strip()
        match = _TIMING.fullmatch(timing)
        if not match or _timestamp_seconds(match[2]) <= _timestamp_seconds(match[1]):
            raise VideoEditError("字幕の時間指定を読み取れません。")
        cues.append(SubtitleCue(timing, " ".join(line.strip() for line in lines[1:])))
    if len(cues) > 200:
        raise VideoEditError("字幕が200行を超えるため、この画面では編集できません。")
    return cues


def write_subtitles(path: Path, cues: list[SubtitleCue], texts: list[str]) -> None:
    if len(cues) != len(texts):
        raise VideoEditError("字幕の行数が変わりました。画面を開き直してください。")
    blocks = []
    for cue, value in zip(cues, texts):
        if not isinstance(value, str) or len(value) > 500:
            raise VideoEditError("字幕は1行500文字以内で入力してください。")
        caption = " ".join(value.split())
        if caption:
            blocks.append(f"{len(blocks) + 1}\n{cue.timing}\n{caption}")
    if not blocks:
        raise VideoEditError("字幕をすべて消す場合は「字幕を表示する」をオフにしてください。")
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def _output_paths(folder: Path) -> tuple[Path, Path]:
    edit_dir = folder / "edits"
    edit_dir.mkdir(exist_ok=True)
    ident = uuid4().hex[:8]
    name = f"edit-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{ident}"
    return edit_dir / f"{name}.mp4", edit_dir / f".pending-{ident}.mp4"


def _save_note(path: Path, note: dict) -> None:
    temp = path.with_suffix(".json.tmp")
    try:
        temp.write_text(json.dumps(note, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, path.with_suffix(".json"))
    except OSError:
        # The MP4 is already committed; optional metadata must not hide success.
        pass
    finally:
        temp.unlink(missing_ok=True)


def _finish_output(output: Path, pending: Path, note: dict) -> Path:
    if not pending.is_file() or pending.stat().st_size == 0:
        raise VideoEditError("編集版の動画が作成されませんでした。")
    os.replace(pending, output)
    _save_note(output, note)
    return output


def quick_edit(
    folder: Path, source: str | Path, *, start: float, end: float,
    volume: float, ffmpeg: str,
) -> Path:
    source = allowed_source(folder, source)
    media = probe_media(source)
    if not all(math.isfinite(value) for value in (start, end, volume)):
        raise VideoEditError("開始・終了・音量には有効な数値を入力してください。")
    if not 0 <= start < end <= media.duration + 0.05 or end - start < 0.5:
        raise VideoEditError("開始と終了を確認してください。残す長さは0.5秒以上にしてください。")
    if not 0 <= volume <= 2:
        raise VideoEditError("音量は0〜200%で指定してください。")
    if not media.has_audio and volume != 1 and start < 0.05 and end >= media.duration - 0.05:
        raise VideoEditError("この動画に音声はありません。カット範囲を変更してください。")
    if start < 0.05 and end >= media.duration - 0.05 and volume == 1:
        raise VideoEditError("開始・終了または音量を変更してください。")
    output, pending = _output_paths(folder)
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source), "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
        "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-threads", "2", "-c:a", "aac", "-b:a", "192k",
    ]
    if media.has_audio:
        command += ["-af", f"volume={volume:.3f}"]
    command += ["-movflags", "+faststart", str(pending)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=600, check=False)
        if result.returncode:
            raise VideoEditError("動画の編集に失敗しました。元動画の形式とMac miniの空き容量を確認してください。")
        return _finish_output(output, pending, {
            "kind": "cut_and_volume", "source": source.name,
            "start": start, "end": end, "volume": volume,
        })
    except subprocess.TimeoutExpired as exc:
        raise VideoEditError("編集が10分以内に終わりませんでした。短い範囲で試してください。") from exc
    except OSError as exc:
        raise VideoEditError("動画処理ツールを起動できませんでした。FFmpegの設定を確認してください。") from exc
    finally:
        pending.unlink(missing_ok=True)


def prepared_assets(folder: Path, index: int, task_state: dict | None = None) -> tuple[Path, Path, Path] | None:
    combined = folder / f"combined-{index}.mp4"
    audio = Path((task_state or {}).get("audio_file") or folder / "audio.mp3")
    subtitle = folder / "subtitle.srt"
    if not combined.is_file() or not audio.is_file():
        return None
    try:
        return _inside_task(folder, combined), _inside_task(folder, audio), subtitle
    except (OSError, VideoEditError):
        return None


def _prepare_uploaded_bgm(folder: Path, data: bytes, suffix: str, ffmpeg: str, duration: float) -> Path:
    if suffix not in {".mp3", ".wav", ".m4a"} or not data or len(data) > 50 * 1024 * 1024:
        raise VideoEditError("BGMはMP3・WAV・M4A形式の50MB以下の音源を選んでください。")
    edit_dir = folder / "edits"
    edit_dir.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".bgm-upload-", suffix=suffix, dir=edit_dir, delete=False) as source:
        source.write(data)
        uploaded = Path(source.name)
    looped = edit_dir / f".bgm-loop-{uuid4().hex}.m4a"
    complete = False
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
             "-stream_loop", "-1", "-protocol_whitelist", "file,pipe",
             "-format_whitelist", "mov,mp3,wav", "-i", str(uploaded),
             "-t", f"{duration:.3f}", "-vn", "-c:a", "aac",
             "-b:a", "192k", str(looped)],
            capture_output=True, timeout=120, check=False,
        )
        if result.returncode or not looped.is_file() or looped.stat().st_size == 0:
            raise VideoEditError("アップロードしたBGMを読み取れません。別の音源を選んでください。")
        complete = True
        return looped
    except subprocess.TimeoutExpired as exc:
        raise VideoEditError("BGMの準備が時間内に終わりませんでした。短い音源で試してください。") from exc
    finally:
        uploaded.unlink(missing_ok=True)
        if not complete:
            looped.unlink(missing_ok=True)


def finish_edit(
    folder: Path, index: int, *, task_state: dict | None,
    subtitle_enabled: bool, subtitle_texts: list[str] | None,
    subtitle_position: str, font_size: int, voice_volume: float,
    bgm_mode: str, bgm_volume: float,
    bgm_upload: bytes | None = None, bgm_suffix: str = "",
) -> tuple[Path, bool]:
    assets = prepared_assets(folder, index, task_state)
    if not assets:
        raise VideoEditError("再仕上げ用の映像・音声素材が残っていません。カットと全体音量は編集できます。")
    if subtitle_position not in {"bottom", "top", "center", "two_thirds_bottom"}:
        raise VideoEditError("字幕位置を選び直してください。")
    if not 30 <= font_size <= 100 or not 0 <= voice_volume <= 2 or not 0 <= bgm_volume <= 1:
        raise VideoEditError("字幕サイズまたは音量を選び直してください。")
    if bgm_mode not in {"original", "none", "upload"}:
        raise VideoEditError("BGMの選択が正しくありません。")
    if bgm_mode == "upload" and bgm_volume <= 0:
        raise VideoEditError("アップロードしたBGMの音量を1%以上にしてください。")

    script_file = folder / "script.json"
    if not script_file.is_file():
        raise VideoEditError("元の動画設定が残っていません。")
    try:
        from app.models.schema import VideoParams

        data = json.loads(script_file.read_text(encoding="utf-8"))
        params = VideoParams.model_validate(data["params"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise VideoEditError("元の動画設定を読み取れません。") from exc
    params.subtitle_enabled = bool(subtitle_enabled)
    params.subtitle_position = subtitle_position
    params.font_size = font_size
    params.voice_volume = voice_volume
    params.bgm_volume = bgm_volume
    if bgm_mode == "none":
        params.bgm_type = ""
    elif bgm_mode == "upload":
        params.bgm_type = "custom"

    combined, audio, subtitle = assets
    if subtitle_enabled and not subtitle.is_file():
        raise VideoEditError("字幕データが残っていません。字幕をオフにするか、元設定から再生成してください。")
    output, pending = _output_paths(folder)
    edited_subtitle = output.with_suffix(".srt")
    if subtitle_enabled and subtitle_texts is not None:
        cues = read_subtitles(subtitle)
        write_subtitles(edited_subtitle, cues, subtitle_texts)
        subtitle = edited_subtitle

    bgm_override = "" if bgm_mode == "none" else None
    uploaded_bgm = None
    if bgm_mode == "original" and params.bgm_type in {"sonilo", "elevenlabs"}:
        matches = list(folder.glob(f"{params.bgm_type}-bgm-{index}.*"))
        if not matches:
            raise VideoEditError("元のBGM音源が残っていません。「BGMなし」を選んでください。")
        bgm_override = str(_inside_task(folder, matches[0]))
    elif bgm_mode == "original" and params.bgm_type not in {"", "random"}:
        from app.services import video

        if not video.get_bgm_file(params.bgm_type, params.bgm_file):
            raise VideoEditError("元のBGM音源が見つかりません。「BGMなし」を選んでください。")
    elif bgm_mode == "upload":
        from app.utils import utils

        uploaded_bgm = _prepare_uploaded_bgm(
            folder, bgm_upload or b"", bgm_suffix,
            utils.get_ffmpeg_binary(), probe_media(combined).duration,
        )
        bgm_override = str(uploaded_bgm)
    try:
        from app.services import video

        bgm_succeeded = video.generate_video(
            video_path=str(combined), audio_path=str(audio),
            subtitle_path=str(subtitle) if subtitle_enabled else "",
            output_file=str(pending), params=params,
            bgm_file_override=bgm_override,
        )
        return _finish_output(output, pending, {
            "kind": "finish", "source": f"final-{index}.mp4",
            "subtitle_enabled": subtitle_enabled,
            "subtitle_position": subtitle_position,
            "font_size": font_size, "voice_volume": voice_volume,
            "bgm_mode": bgm_mode, "bgm_volume": bgm_volume,
        }), bgm_succeeded
    except VideoEditError:
        raise
    except Exception as exc:
        raise VideoEditError("再仕上げに失敗しました。字幕・音声・BGMの設定とMac miniの空き容量を確認してください。") from exc
    finally:
        pending.unlink(missing_ok=True)
        if uploaded_bgm is not None:
            uploaded_bgm.unlink(missing_ok=True)
