"""Streamlit editor for local, already generated MoneyPrinterTurbo videos."""

from pathlib import Path

import streamlit as st

from .video_edit import (
    VideoEditError, allowed_source, edited_videos, finish_edit, original_videos,
    prepared_assets, probe_media, quick_edit, read_subtitles, task_directory,
)


def _close_editor() -> None:
    st.session_state.pop("video_edit_candidate_id", None)


def _show_result(folder: Path, task_id: str) -> None:
    result = st.session_state.get(f"video_edit_result_{task_id}")
    if not result:
        return
    try:
        path = allowed_source(folder, result)
    except (OSError, VideoEditError):
        st.session_state.pop(f"video_edit_result_{task_id}", None)
        return
    st.success("編集版を保存しました。元の動画は残っています。")
    st.video(str(path))
    with path.open("rb") as source:
        st.download_button(
            "編集版をダウンロード", data=source, file_name=path.name,
            mime="video/mp4", key=f"video_edit_download_{task_id}",
            use_container_width=True,
        )


def _cut_editor(folder: Path, task_id: str, originals: list[Path], edits: list[Path]) -> None:
    from app.utils import utils

    choices = {f"元動画 {index + 1} · {path.name}": path for index, path in enumerate(originals)}
    choices.update({f"編集版 · {path.name}": path for path in edits})
    selected = st.selectbox("編集する動画", list(choices), key=f"video_edit_source_{task_id}")
    source = choices[selected]
    media = probe_media(source)
    st.video(str(source))
    st.caption(f"動画の長さ：{media.duration:.1f}秒。元動画と過去の編集版は上書きしません。")
    start = st.number_input(
        "残す部分の開始（秒）", min_value=0.0, max_value=max(0.0, media.duration - 0.5),
        value=0.0, step=0.1, key=f"video_edit_start_{task_id}_{source.stem}",
    )
    end = st.number_input(
        "残す部分の終了（秒）", min_value=0.5, max_value=media.duration,
        value=media.duration, step=0.1, key=f"video_edit_end_{task_id}_{source.stem}",
    )
    volume = st.slider(
        "動画全体の音量", min_value=0, max_value=200, value=100, step=5,
        disabled=not media.has_audio, key=f"video_edit_volume_{task_id}_{source.stem}",
    )
    if not media.has_audio:
        st.caption("この動画には音声がないため、音量は変更できません。")
    st.caption("この編集では映像の前後と、完成動画に混ざった音声全体を調整します。")
    if st.button("カット・音量を反映して保存", type="primary", use_container_width=True,
                 key=f"video_edit_cut_save_{task_id}"):
        try:
            with st.spinner("編集版を作成しています…"):
                output = quick_edit(
                    folder, source, start=start, end=end, volume=volume / 100,
                    ffmpeg=utils.get_ffmpeg_binary(),
                )
            st.session_state[f"video_edit_result_{task_id}"] = str(output)
        except VideoEditError as exc:
            st.error(str(exc))


def _finish_editor(folder: Path, task_id: str, originals: list[Path]) -> None:
    from app.services import state as sm

    choices = {f"元動画 {path.stem.split('-')[1]}": (int(path.stem.split('-')[1]), path) for path in originals}
    selected = st.selectbox("仕上げ直す元動画", list(choices), key=f"video_finish_source_{task_id}")
    index, original = choices[selected]
    try:
        state = sm.state.get_task(task_id) or {}
    except Exception:
        state = {}
    assets = prepared_assets(folder, index, state)
    if not assets:
        st.info("再仕上げ用の映像・音声素材が残っていません。「カット・全体音量」は編集できます。")
        return
    st.video(str(original))
    st.caption("保存済みの映像と音声を使って仕上げ直します。文章AIや素材サービスへの新しい依頼は発生しません。")

    script_path = folder / "script.json"
    try:
        import json

        settings = json.loads(script_path.read_text(encoding="utf-8"))["params"]
    except (OSError, ValueError, KeyError, TypeError):
        st.error("元の動画設定を読み取れません。")
        return

    cues = read_subtitles(assets[2])
    subtitle_on = st.checkbox(
        "字幕を表示する", value=bool(cues) and bool(settings.get("subtitle_enabled", True)),
        disabled=not cues, key=f"video_finish_subtitles_{task_id}_{index}",
    )
    subtitle_texts = None
    if subtitle_on and cues:
        rows = st.data_editor(
            [{"時間": cue.timing, "字幕": cue.text} for cue in cues],
            disabled=["時間"], num_rows="fixed", hide_index=True,
            use_container_width=True, key=f"video_finish_cues_{task_id}_{index}",
        )
        if hasattr(rows, "to_dict"):
            rows = rows.to_dict("records")
        subtitle_texts = [str(row["字幕"]) for row in rows]
    position_labels = {
        "bottom": "下", "top": "上", "center": "中央",
        "two_thirds_bottom": "上から3分の1",
    }
    saved_position = settings.get("subtitle_position", "bottom")
    positions = list(position_labels)
    position = st.selectbox(
        "字幕の位置", positions, index=positions.index(saved_position) if saved_position in positions else 0,
        format_func=lambda value: position_labels[value], disabled=not subtitle_on,
        key=f"video_finish_position_{task_id}_{index}",
    )
    font_size = st.slider(
        "字幕の大きさ", min_value=30, max_value=100,
        value=max(30, min(100, int(settings.get("font_size") or 60))),
        disabled=not subtitle_on, key=f"video_finish_font_{task_id}_{index}",
    )
    saved_voice_volume = settings.get("voice_volume")
    voice_volume = st.slider(
        "ナレーション音量", min_value=0, max_value=200,
        value=max(0, min(200, round(float(1 if saved_voice_volume is None else saved_voice_volume) * 100))),
        step=5, key=f"video_finish_voice_{task_id}_{index}",
    )
    original_bgm = bool(settings.get("bgm_type"))
    bgm_modes = (["元のBGM設定"] if original_bgm else []) + ["BGMなし", "別の音源をアップロード"]
    bgm_label = st.radio(
        "BGM", bgm_modes, horizontal=True, key=f"video_finish_bgm_{task_id}_{index}",
    )
    bgm_volume = st.slider(
        "BGM音量", min_value=0, max_value=100,
        value=max(0, min(100, round(float(0.2 if settings.get("bgm_volume") is None else settings["bgm_volume"]) * 100))),
        step=5, disabled=bgm_label == "BGMなし",
        key=f"video_finish_bgm_volume_{task_id}_{index}",
    )
    uploaded_bgm = None
    if bgm_label == "別の音源をアップロード":
        uploaded_bgm = st.file_uploader(
            "BGM音源（MP3・WAV・M4A、50MB以下）", type=["mp3", "wav", "m4a"],
            key=f"video_finish_bgm_upload_{task_id}_{index}",
        )
        st.caption("音源が短い場合は動画の長さまで繰り返します。")
    if bgm_label == "元のBGM設定" and settings.get("bgm_type") == "random":
        st.caption("元のBGMがランダム選択だったため、同じ曲になるとは限りません。")
    st.caption("台本・読み上げ内容・映像素材を変える場合は、タスク管理の「再生成」で設定を呼び出してください。")
    if st.button("字幕・音量・BGMを反映して保存", type="primary", use_container_width=True,
                 key=f"video_finish_save_{task_id}"):
        try:
            with st.spinner("保存済み素材から動画を再仕上げしています…"):
                output, bgm_succeeded = finish_edit(
                    folder, index, task_state=state,
                    subtitle_enabled=subtitle_on, subtitle_texts=subtitle_texts,
                    subtitle_position=position, font_size=font_size,
                    voice_volume=voice_volume / 100,
                    bgm_mode=("original" if bgm_label == "元のBGM設定" else
                              "upload" if bgm_label == "別の音源をアップロード" else "none"),
                    bgm_volume=bgm_volume / 100,
                    bgm_upload=uploaded_bgm.getvalue() if uploaded_bgm else None,
                    bgm_suffix=Path(uploaded_bgm.name).suffix.lower() if uploaded_bgm else "",
                )
            st.session_state[f"video_edit_result_{task_id}"] = str(output)
            if not bgm_succeeded:
                st.warning("BGMを混ぜられなかったため、編集版はBGMなしで保存しました。")
        except VideoEditError as exc:
            st.error(str(exc))


@st.dialog("完成動画を手直し", width="large", on_dismiss=_close_editor)
def render_editor_dialog(task_id: str) -> None:
    from app.utils import utils

    try:
        folder = task_directory(utils.task_dir(), task_id)
        originals = original_videos(folder)
        edits = edited_videos(folder)
        if not originals:
            st.error("完成動画が見つかりません。")
            return
        if st.button("閉じる", key=f"video_edit_close_{task_id}"):
            _close_editor()
            st.rerun(scope="app")
        mode = st.radio(
            "手直しの種類", ["カット・全体音量", "字幕・ナレーション・BGM"],
            horizontal=True, key=f"video_edit_mode_{task_id}",
        )
        if mode == "カット・全体音量":
            _cut_editor(folder, task_id, originals, edits)
        else:
            _finish_editor(folder, task_id, originals)
        _show_result(folder, task_id)
    except VideoEditError as exc:
        st.error(str(exc))
