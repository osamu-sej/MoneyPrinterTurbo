import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codex_overlay"))

from mpt_codex.video_edit import (
    VideoEditError, _prepare_uploaded_bgm, allowed_source, edited_videos,
    finish_edit, original_videos,
    probe_media, quick_edit, read_subtitles, task_directory, write_subtitles,
)


class VideoEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "task-123"
        self.folder.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_srt_text_can_be_replaced_without_changing_timing(self):
        source = self.folder / "subtitle.srt"
        source.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\n古い字幕\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\n次の字幕\n",
            encoding="utf-8",
        )
        cues = read_subtitles(source)
        destination = self.folder / "edited.srt"
        write_subtitles(destination, cues, ["新しい字幕", "次の字幕"])
        updated = read_subtitles(destination)
        self.assertEqual([cue.timing for cue in updated], [cue.timing for cue in cues])
        self.assertEqual(updated[0].text, "新しい字幕")
        self.assertEqual(read_subtitles(source)[0].text, "古い字幕")

    def test_files_outside_task_are_rejected(self):
        other = self.root / "secret.mp4"
        other.write_bytes(b"private")
        self.assertEqual(task_directory(self.root, "task-123"), self.folder.resolve())
        with self.assertRaises(VideoEditError):
            task_directory(self.root, "../other")
        with self.assertRaises(VideoEditError):
            allowed_source(self.folder, other)
        (self.folder / "final-1.mp4").symlink_to(other)
        with self.assertRaises(VideoEditError):
            original_videos(self.folder)

    def test_quick_edit_creates_a_separate_playable_video(self):
        from app.utils import utils

        ffmpeg = utils.get_ffmpeg_binary()
        source = self.folder / "final-1.mp4"
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=15",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
             "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", str(source)],
            check=True, capture_output=True, timeout=30,
        )
        output = quick_edit(self.folder, source, start=0.5, end=1.5, volume=0.5, ffmpeg=ffmpeg)
        self.assertEqual(original_videos(self.folder), [source.resolve()])
        self.assertEqual(edited_videos(self.folder), [output.resolve()])
        self.assertTrue(source.is_file())
        media = probe_media(output)
        self.assertTrue(media.has_audio)
        self.assertAlmostEqual(media.duration, 1.0, delta=0.2)
        with self.assertRaises(VideoEditError):
            quick_edit(self.folder, source, start=0, end=2, volume=1, ffmpeg=ffmpeg)

    def test_short_uploaded_bgm_is_looped_to_video_length(self):
        from app.utils import utils

        ffmpeg = utils.get_ffmpeg_binary()
        source = self.folder / "short.mp3"
        subprocess.run(
            [ffmpeg, "-v", "error", "-y", "-f", "lavfi", "-i",
             "sine=frequency=220:sample_rate=44100", "-t", "0.5", str(source)],
            check=True, capture_output=True, timeout=30,
        )
        looped = _prepare_uploaded_bgm(self.folder, source.read_bytes(), ".mp3", ffmpeg, 1.5)
        self.assertTrue(looped.is_file())
        self.assertEqual(list((self.folder / "edits").glob(".bgm-upload-*")), [])
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", str(looped)], capture_output=True,
            text=True, timeout=10,
        )
        self.assertIn("Duration: 00:00:01.5", result.stderr)

    def test_finish_uses_prepared_assets_and_preserves_original(self):
        original = self.folder / "final-1.mp4"
        original.write_bytes(b"original")
        (self.folder / "combined-1.mp4").write_bytes(b"prepared footage")
        (self.folder / "audio.mp3").write_bytes(b"prepared narration")
        (self.folder / "subtitle.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\n古い字幕\n", encoding="utf-8"
        )
        (self.folder / "script.json").write_text(
            json.dumps({"params": {"video_subject": "sample", "bgm_type": "random"}}), encoding="utf-8"
        )
        schema = ModuleType("app.models.schema")
        schema.VideoParams = SimpleNamespace(model_validate=lambda value: SimpleNamespace(**value))
        video = ModuleType("app.services.video")
        def fake_render(**kwargs):
            self.assertEqual(kwargs["params"].bgm_type, "")
            self.assertEqual(kwargs["params"].voice_volume, 0.5)
            self.assertEqual(read_subtitles(Path(kwargs["subtitle_path"]))[0].text, "新しい字幕")
            Path(kwargs["output_file"]).write_bytes(b"new video")
            return True

        video.generate_video = fake_render
        with patch.dict(sys.modules, {"app.models.schema": schema, "app.services.video": video}):
            output, bgm_ok = finish_edit(
                self.folder, 1, task_state={}, subtitle_enabled=True,
                subtitle_texts=["新しい字幕"], subtitle_position="bottom",
                font_size=60, voice_volume=0.5, bgm_mode="none", bgm_volume=0,
            )
        self.assertTrue(bgm_ok)
        self.assertEqual(output.read_bytes(), b"new video")
        self.assertEqual(original.read_bytes(), b"original")
        self.assertEqual(read_subtitles(self.folder / "subtitle.srt")[0].text, "古い字幕")


if __name__ == "__main__":
    unittest.main()
