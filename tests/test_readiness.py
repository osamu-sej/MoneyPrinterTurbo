import runpy
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codex_overlay"))

from mpt_codex.readiness import (
    OPTIONAL_FEATURES, codex_logged_in, first_video_steps, render_readiness,
    local_material_resolution_issues, needs_text_ai, setup_issues,
)
from mpt_codex.service_guide import SECTION_INTROS, VIDEO_GUIDES, VIDEO_NAMES, llm_guide


class SetupIssuesTests(unittest.TestCase):
    def test_generate_button_only_blocks_known_prerequisite_failures(self):
        class FakeStreamlit:
            def __init__(self):
                self.session_state = {"llm_provider_select": "codex_app_server"}

            def container(self, **_kwargs):
                return self

            def expander(self, *_args, **_kwargs):
                return self

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def markdown(self, *_args, **_kwargs):
                pass

            def caption(self, *_args, **_kwargs):
                pass

            def warning(self, *_args, **_kwargs):
                pass

            def button(self, *_args, **_kwargs):
                return False

        fake = FakeStreamlit()
        with patch.dict(sys.modules, {"streamlit": fake}), patch(
            "mpt_codex.readiness.shutil.which", return_value="/usr/bin/codex"
        ), patch("mpt_codex.readiness.codex_logged_in", return_value=False):
            self.assertTrue(render_readiness("local", {}, False, lambda: None, subject="京都"))
            self.assertTrue(render_readiness("local", {}, True, lambda: None, subject="京都"))
            self.assertTrue(render_readiness("local", {}, True, lambda: None, script=""))
            self.assertFalse(render_readiness("local", {}, True, lambda: None, script="手入力の台本"))
            self.assertTrue(render_readiness("pexels", {}, False, lambda: None, script="手入力の台本", terms="京都"))
            self.assertFalse(render_readiness(
                "pexels", {"pexels_api_keys": ["configured"]}, False,
                lambda: None, script="手入力の台本", terms="京都",
            ))
            small_image = BytesIO()
            Image.new("RGB", (200, 154)).save(small_image, format="PNG")
            small_image.name = "thumbnail.png"
            self.assertTrue(render_readiness(
                "local", {}, True, lambda: None, script="手入力の台本",
                uploaded_files=[small_image],
            ))

    def test_missing_codex_login_and_pexels_key_are_actionable(self):
        issues = setup_issues(
            "pexels", "codex_app_server", {}, executable="/usr/bin/codex", logged_in=False
        )
        self.assertEqual(len(issues), 2)
        self.assertIn("codex login", issues[0])
        self.assertIn("Pexels", issues[1])

    def test_ready_setup_has_no_issues(self):
        issues = setup_issues(
            "pexels", "codex_app_server", {"pexels_api_keys": ["configured"]},
            executable="/usr/bin/codex", logged_in=True,
        )
        self.assertEqual(issues, [])

    def test_empty_key_list_is_missing(self):
        issues = setup_issues(
            "pexels", "codex_app_server", {"pexels_api_keys": []},
            executable="/usr/bin/codex", logged_in=True,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("Pexels", issues[0])

    def test_local_source_requires_upload(self):
        issues = setup_issues(
            "local", "codex_app_server", {}, executable="/usr/bin/codex",
            logged_in=True, has_local_materials=False,
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("アップロード", issues[0])

    def test_manual_script_and_local_material_do_not_require_ai_login(self):
        self.assertFalse(needs_text_ai("自分で書いた台本", "", "local"))
        issues = setup_issues(
            "local", "codex_app_server", {}, executable=None, logged_in=False,
            has_local_materials=True, needs_ai=False,
        )
        self.assertEqual(issues, [])
        steps = first_video_steps(
            subject="", script="自分で書いた台本", terms="", video_source="local",
            provider="codex_app_server", app_config={}, executable=None,
            logged_in=False, has_local_materials=True,
        )
        self.assertEqual([ready for _, ready, _ in steps], [True, True, True])
        self.assertIn("呼び出しは不要", steps[1][2])
        invalid_steps = first_video_steps(
            subject="", script="自分で書いた台本", terms="", video_source="local",
            provider="codex_app_server", app_config={}, executable=None,
            logged_in=False, has_local_materials=True, local_material_valid=False,
        )
        self.assertFalse(invalid_steps[2][1])

    def test_topic_only_needs_ai_and_selected_stock_key(self):
        steps = first_video_steps(
            subject="京都", script="", terms="", video_source="pexels",
            provider="codex_app_server", app_config={}, executable=None,
            logged_in=False, has_local_materials=False,
        )
        self.assertEqual([ready for _, ready, _ in steps], [True, False, False])
        self.assertIn("Pexels", steps[2][2])

    def test_optional_help_explains_effects(self):
        self.assertGreaterEqual(len(OPTIONAL_FEATURES), 6)
        for setting, effect in OPTIONAL_FEATURES:
            self.assertTrue(setting)
            self.assertTrue(effect)

    def test_login_check_fails_closed(self):
        with patch("mpt_codex.readiness.subprocess.run", side_effect=OSError):
            self.assertFalse(codex_logged_in("/usr/bin/codex"))

    def test_small_uploaded_image_is_rejected_before_generation(self):
        image_bytes = BytesIO()
        Image.new("RGB", (200, 154)).save(image_bytes, format="PNG")
        image_bytes.name = "thumbnail.png"
        issues = local_material_resolution_issues([image_bytes], [])
        self.assertEqual(len(issues), 1)
        self.assertIn("200×154px", issues[0])

    def test_sufficient_uploaded_image_is_accepted(self):
        image_bytes = BytesIO()
        Image.new("RGB", (480, 480)).save(image_bytes, format="PNG")
        image_bytes.name = "original.png"
        self.assertEqual(local_material_resolution_issues([image_bytes], []), [])

    def test_saved_small_image_is_rejected_on_next_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "saved.png"
            Image.new("RGB", (200, 154)).save(image_path)
            with patch("app.utils.utils.storage_dir", return_value=directory):
                issues = local_material_resolution_issues([], [{"url": str(image_path)}])
        self.assertEqual(len(issues), 1)
        self.assertIn("200×154px", issues[0])


class ServiceGuideTests(unittest.TestCase):
    def test_each_main_setting_has_beginner_explanation(self):
        self.assertEqual(set(SECTION_INTROS), {"script", "video", "audio", "subtitle"})
        self.assertTrue(all("最初" in text or "既定" in text for text in SECTION_INTROS.values()))

    def test_every_video_source_has_explanation_and_safe_link(self):
        self.assertEqual(set(VIDEO_GUIDES), set(VIDEO_NAMES))
        for source, guide in VIDEO_GUIDES.items():
            self.assertTrue(guide.capability, source)
            self.assertTrue(guide.setup, source)
            for _, url in guide.links:
                self.assertTrue(url.startswith("https://"), source)

    def test_codex_setup_distinguishes_other_api_keys(self):
        provider = SimpleNamespace(provider_id="codex_app_server")
        guide = llm_guide(provider)
        self.assertIn("codex login", guide.setup)
        self.assertIn("別設定", guide.setup)


class WebUIPatchTests(unittest.TestCase):
    def test_patch_is_idempotent_and_uses_exact_anchor(self):
        module = runpy.run_path(str(ROOT / "scripts" / "patch-webui.py"))
        anchor = module["ANCHOR"]
        language_anchor = module["LANGUAGE_ANCHOR"]
        tips_anchor = module["TIPS_ANCHOR"]
        region_anchor = module["REGION_ANCHOR"]
        button_anchor = module["BUTTON_ANCHOR"]
        llm_guide_anchor = module["LLM_GUIDE_ANCHOR"]
        video_guide_anchor = module["VIDEO_GUIDE_ANCHOR"]
        audio_guide_anchor = module["AUDIO_GUIDE_ANCHOR"]
        material_directory_anchor = module["MATERIAL_DIRECTORY_ANCHOR"]
        failed_task_anchor = module["FAILED_TASK_ANCHOR"]
        task_summary_anchor = module["TASK_SUMMARY_ANCHOR"]
        task_row_anchor = module["TASK_ROW_ANCHOR"]
        section_anchors = module["SECTION_INTRO_ANCHORS"]
        patch_text = module["patch_text"]
        original = (
            f"before\n{tips_anchor}\n{region_anchor}\n{region_anchor}\n"
            f"{tips_anchor}\n{language_anchor}\n{llm_guide_anchor}"
            f"{material_directory_anchor}{video_guide_anchor}"
            f"{audio_guide_anchor}{''.join(section_anchors.values())}"
            f"{failed_task_anchor}{task_summary_anchor}{task_row_anchor}"
            f"{anchor}{button_anchor}after\n"
        )
        patched = patch_text(original)
        self.assertIn("render_readiness", patched)
        self.assertIn("subject=params.video_subject, script=params.video_script, terms=params.video_terms", patched)
        self.assertIn("render_video_guide", patched)
        self.assertIn("render_llm_guide", patched)
        self.assertIn("render_tts_guide", patched)
        self.assertIn("render_material_directory", patched)
        self.assertIn("render_failure_guidance(task)", patched)
        self.assertIn("render_failure_guidance(task, compact=True)", patched)
        self.assertIn('"failed_stage": task.get("failed_stage")', patched)
        self.assertEqual(patched.count("render_section_intro("), 4)
        self.assertIn("disabled=generation_blocked", patched)
        self.assertIn("_mpt_language_synced", patched)
        self.assertEqual(patched.count('"ja"} else "en"'), 2)
        self.assertEqual(patched.count('prefer_international=tips_language != "zh"'), 2)
        self.assertEqual(patch_text(patched), patched)
        previous_insertion = module["PREVIOUS_INSERTION"]
        self.assertIn("subject=params.video_subject", patch_text(original.replace(anchor, previous_insertion)))
        current = patched.replace(module["INSERTION"], module["CURRENT_INSERTION"]).replace(
            module["BUTTON_INSERTION"], module["CURRENT_BUTTON_INSERTION"]
        )
        self.assertEqual(patch_text(current), patched)
        with self.assertRaises(ValueError):
            patch_text("unknown layout")

    def test_mobile_style_patch_is_idempotent(self):
        module = runpy.run_path(str(ROOT / "scripts" / "patch-webui.py"))
        mobile_style = (ROOT / "webui" / "mobile.css").read_text(encoding="utf-8")
        patch_style = module["patch_style"]
        original = "body { color: black; }\n"
        patched = patch_style(original, mobile_style)
        self.assertIn("mpt-mobile-v1", patched)
        self.assertEqual(patch_style(patched, mobile_style), patched)


if __name__ == "__main__":
    unittest.main()
