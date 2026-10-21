import runpy
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codex_overlay"))

from mpt_codex.readiness import (
    codex_logged_in, local_material_resolution_issues, setup_issues,
)


class SetupIssuesTests(unittest.TestCase):
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


class WebUIPatchTests(unittest.TestCase):
    def test_patch_is_idempotent_and_uses_exact_anchor(self):
        module = runpy.run_path(str(ROOT / "scripts" / "patch-webui.py"))
        anchor = module["ANCHOR"]
        language_anchor = module["LANGUAGE_ANCHOR"]
        tips_anchor = module["TIPS_ANCHOR"]
        region_anchor = module["REGION_ANCHOR"]
        button_anchor = module["BUTTON_ANCHOR"]
        patch_text = module["patch_text"]
        original = f"before\n{tips_anchor}\n{region_anchor}\n{region_anchor}\n{tips_anchor}\n{language_anchor}\n{anchor}{button_anchor}after\n"
        patched = patch_text(original)
        self.assertIn("render_readiness", patched)
        self.assertIn("disabled=local_resolution_blocked", patched)
        self.assertIn("_mpt_language_synced", patched)
        self.assertEqual(patched.count('"ja"} else "en"'), 2)
        self.assertEqual(patched.count('prefer_international=tips_language != "zh"'), 2)
        self.assertEqual(patch_text(patched), patched)
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
