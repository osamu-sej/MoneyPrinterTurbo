#!/usr/bin/env bash
# Start the local WebUI at login and restart it if it exits unexpectedly.
set -euo pipefail

if [ "$(uname)" != Darwin ]; then
  echo "このスクリプトはmacOS専用です。" >&2
  exit 1
fi

mpt_dir="${MPT_DIR:-$HOME/mpt}"
python="$mpt_dir/.venv/bin/python"
mpt="$mpt_dir/.venv/bin/mpt"
if [ ! -x "$python" ] || [ ! -x "$mpt" ]; then
  echo "MoneyPrinterTurboが見つかりません。先に scripts/install.sh を実行してください。" >&2
  exit 1
fi

label="com.osamu.moneyprinterturbo.webui"
agent_dir="$HOME/Library/LaunchAgents"
log_dir="$mpt_dir/home/logs"
plist="$agent_dir/$label.plist"
mkdir -p "$agent_dir" "$log_dir"

MPT_AGENT_PLIST="$plist" MPT_AGENT_DIR="$mpt_dir" MPT_AGENT_LOG_DIR="$log_dir" \
  "$python" - <<'PY'
import os
import pathlib
import plistlib

root = pathlib.Path(os.environ["MPT_AGENT_DIR"])
log_dir = pathlib.Path(os.environ["MPT_AGENT_LOG_DIR"])
data = {
    "Label": "com.osamu.moneyprinterturbo.webui",
    "ProgramArguments": [
        str(root / ".venv/bin/mpt"), "webui", "--host", "127.0.0.1", "--port", "8501"
    ],
    "WorkingDirectory": str(root),
    "EnvironmentVariables": {
        "HOME": str(pathlib.Path.home()),
        "MPT_HOME": str(root / "home"),
        "MPT_CODEX_APP_SERVER": "1",
        "PYTHONPATH": str(root / "codex_overlay"),
        "PATH": ":".join([
            str(pathlib.Path.home() / ".local/bin"),
            "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin",
        ]),
    },
    "RunAtLoad": True,
    "KeepAlive": True,
    "StandardOutPath": str(log_dir / "webui.out.log"),
    "StandardErrorPath": str(log_dir / "webui.err.log"),
}
path = pathlib.Path(os.environ["MPT_AGENT_PLIST"])
with path.open("wb") as stream:
    plistlib.dump(data, stream)
PY

uid="$(id -u)"
launchctl bootout "gui/$uid/$label" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$uid" "$plist"
launchctl enable "gui/$uid/$label"
launchctl kickstart -k "gui/$uid/$label"
echo "ログイン時の自動起動を設定しました: $plist"
echo "状態確認: launchctl print gui/$uid/$label"
