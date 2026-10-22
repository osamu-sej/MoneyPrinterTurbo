import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codex_overlay"))

from mpt_codex.failure_guidance import diagnose_failure


class FailureGuidanceTests(unittest.TestCase):
    def test_local_material_failure_explains_size_and_replacement(self):
        advice = diagnose_failure({
            "failed_stage": "materials",
            "error": "no valid local video materials were found",
        })
        self.assertIn("ローカル素材", advice.reason)
        self.assertIn("480px", advice.actions[0])
        self.assertEqual(advice.stage, "映像素材")

    def test_missing_ffmpeg_has_install_action(self):
        advice = diagnose_failure({
            "failed_stage": "preflight",
            "error": "ffmpeg is not available; install ffmpeg",
        })
        self.assertIn("FFmpeg", advice.reason)
        self.assertIn("FFmpeg設定", advice.actions[0])

    def test_codex_cli_failure_has_specific_recovery(self):
        advice = diagnose_failure({
            "failed_stage": "script",
            "error": "Codex app server: Codex CLI is not installed or not on PATH",
        })
        self.assertIn("Codex CLI", advice.reason)
        self.assertIn("codex login", advice.actions[0])

    def test_authentication_and_rate_limit_are_distinct(self):
        auth = diagnose_failure({"failed_stage": "script", "error": "401 unauthorized"})
        limit = diagnose_failure({"failed_stage": "script", "error": "rate limit exceeded"})
        self.assertIn("認証", auth.reason)
        self.assertIn("利用枠", limit.reason)

    def test_local_storage_failures_are_actionable(self):
        denied = diagnose_failure({"failed_stage": "materials", "error": "Operation not permitted"})
        full = diagnose_failure({"failed_stage": "video", "error": "No space left on device"})
        self.assertIn("アクセス", denied.reason)
        self.assertIn("空き容量", full.reason)

    def test_paid_remote_task_requires_check_before_retry(self):
        advice = diagnose_failure({
            "failed_stage": "materials",
            "error": "download timed out",
            "wavespeed_prediction_id": "prediction-123",
        })
        self.assertTrue(advice.remote_job_exists)
        self.assertIn("通信", advice.reason)
        summary_advice = diagnose_failure({
            "failed_stage": "materials", "error": "download timed out",
            "remote_job_exists": True,
        })
        self.assertTrue(summary_advice.remote_job_exists)

    def test_unknown_error_does_not_invent_cause_or_reveal_credentials(self):
        advice = diagnose_failure({
            "failed_stage": "video",
            "error": "unexpected fault: api_key=private-value at /Users/person/mpt",
        })
        self.assertIn("原因を特定できません", advice.reason)
        self.assertNotIn("private-value", advice.detail)
        self.assertNotIn("/Users/person", advice.detail)

    def test_missing_error_offers_log_check(self):
        advice = diagnose_failure({"failed_stage": "pipeline", "error": None})
        self.assertIn("保存されていません", advice.reason)
        self.assertIn("ログ", advice.actions[0])


if __name__ == "__main__":
    unittest.main()
