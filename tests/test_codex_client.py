import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codex_overlay"))

from mpt_codex.client import CodexError, generate


FAKE_SERVER = '''#!{python}
import json
import sys

def send(value):
    print(json.dumps(value), flush=True)

for line in sys.stdin:
    request = json.loads(line)
    method = request['method']
    if method == 'initialize':
        send({{'id': request['id'], 'result': {{}}}})
    elif method == 'model/list':
        send({{'id': request['id'], 'result': {{'data': [{{'model': 'test-model', 'isDefault': True}}]}}}})
    elif method == 'thread/start':
        assert request['params']['model'] == 'test-model'
        assert request['params']['sandbox'] == 'read-only'
        assert request['params']['approvalPolicy'] == 'never'
        assert request['params']['ephemeral'] is True
        send({{'id': request['id'], 'result': {{'thread': {{'id': 'test-thread'}}}}}})
    elif method == 'turn/start':
        assert request['params']['threadId'] == 'test-thread'
        # An event can arrive before the RPC response.
        send({{'method': 'item/agentMessage/delta', 'params': {{'delta': 'hello'}}}})
        send({{'id': request['id'], 'result': {{'turn': {{'id': 'test-turn'}}}}}})
        send({{'method': 'turn/completed', 'params': {{'turn': {{'status': '{status}', 'error': {{'message': 'failed'}}}}}}}})
'''


class CodexClientTests(unittest.TestCase):
    def _run(self, status):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex-fake"
            executable.write_text(
                FAKE_SERVER.format(python=sys.executable, status=status),
                encoding="utf-8",
            )
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
            with patch.dict(os.environ, {"MPT_CODEX_CLI": str(executable)}):
                return generate("test prompt", timeout=5)

    def test_completed_turn_returns_text(self):
        self.assertEqual(self._run("completed"), "hello")

    def test_failed_turn_is_not_treated_as_text(self):
        with self.assertRaisesRegex(CodexError, "failed"):
            self._run("failed")


if __name__ == "__main__":
    unittest.main()
