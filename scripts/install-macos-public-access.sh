#!/usr/bin/env bash
# Publish only the access-key gateway through Tailscale Funnel on port 8443.
# The existing private Serve on port 443 remains available.
set -euo pipefail

if [ "$(uname)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  echo "この導入スクリプトはApple SiliconのmacOS専用です。" >&2
  exit 1
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mpt_dir="${MPT_DIR:-$HOME/mpt}"
python="$mpt_dir/.venv/bin/python"
if [ ! -x "$python" ] || [ ! -f "$repo_dir/deploy/Caddyfile.mac-public" ]; then
  echo "MoneyPrinterTurboの導入先または公開ゲートウェイ設定が見つかりません。" >&2
  exit 1
fi

if command -v tailscale >/dev/null 2>&1; then
  tailscale_cli="$(command -v tailscale)"
elif [ -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]; then
  tailscale_cli=/Applications/Tailscale.app/Contents/MacOS/Tailscale
else
  echo "Mac miniにTailscaleが見つかりません。" >&2
  exit 1
fi
export TAILSCALE_BE_CLI=1
if ! "$tailscale_cli" status --json >/dev/null; then
  echo "Mac miniのTailscale接続を確認できません。" >&2
  exit 1
fi

mkdir -p "$mpt_dir/bin" "$mpt_dir/home/logs" "$HOME/Library/LaunchAgents"
key_file="$mpt_dir/home/public-access.key"
link_file="$mpt_dir/home/public-access-link.txt"
umask 077
if [ ! -s "$key_file" ]; then
  "$python" - "$key_file" <<'PY'
import pathlib
import secrets
import sys

pathlib.Path(sys.argv[1]).write_text(secrets.token_urlsafe(32), encoding="ascii")
PY
fi
chmod 600 "$key_file"

caddy="$mpt_dir/bin/caddy"
if [ ! -x "$caddy" ] || ! "$caddy" version 2>/dev/null | grep -q '^v2\.11\.7 '; then
  archive_dir="$(mktemp -d)"
  trap 'rm -rf "$archive_dir"' EXIT
  archive="$archive_dir/caddy_2.11.7_mac_arm64.tar.gz"
  curl -fsSL --retry 3 \
    'https://github.com/caddyserver/caddy/releases/download/v2.11.7/caddy_2.11.7_mac_arm64.tar.gz' \
    -o "$archive"
  expected_sha512='68f592df8f0ec058fbdb9b137b64e9a0aa792d28c06e1e3b9ec12d0e7fb371683a54e73ef6d8e6d0dd70dc6b941a5b5d5b73faedd3f89de119ad2eb78bdc668e'
  printf '%s  %s\n' "$expected_sha512" "$archive" | shasum -a 512 -c - >/dev/null
  tar -xzf "$archive" -C "$archive_dir" caddy
  install -m 755 "$archive_dir/caddy" "$caddy"
fi

install -m 644 "$repo_dir/deploy/Caddyfile.mac-public" "$mpt_dir/Caddyfile.mac-public"
install -m 755 "$repo_dir/scripts/run-macos-public-gateway.sh" "$mpt_dir/run-macos-public-gateway.sh"
MPT_CADDY_BIN="$caddy" MPT_CADDY_CONFIG="$mpt_dir/Caddyfile.mac-public" MPT_CADDY_KEY="$key_file" \
  "$python" - <<'PY'
import os
import pathlib
import subprocess

env = os.environ.copy()
env["MPT_ACCESS_KEY"] = pathlib.Path(env["MPT_CADDY_KEY"]).read_text(encoding="ascii").strip()
subprocess.run(
    [env["MPT_CADDY_BIN"], "validate", "--config", env["MPT_CADDY_CONFIG"], "--adapter", "caddyfile"],
    env=env,
    stdout=subprocess.DEVNULL,
    check=True,
)
PY

label=com.osamu.moneyprinterturbo.public-gateway
plist="$HOME/Library/LaunchAgents/$label.plist"
MPT_AGENT_PLIST="$plist" MPT_AGENT_DIR="$mpt_dir" MPT_AGENT_LOG_DIR="$mpt_dir/home/logs" \
  "$python" - <<'PY'
import os
import pathlib
import plistlib

root = pathlib.Path(os.environ["MPT_AGENT_DIR"])
data = {
    "Label": "com.osamu.moneyprinterturbo.public-gateway",
    "ProgramArguments": [str(root / "run-macos-public-gateway.sh")],
    "WorkingDirectory": str(root),
    "EnvironmentVariables": {"HOME": str(pathlib.Path.home()), "MPT_DIR": str(root)},
    "RunAtLoad": True,
    "KeepAlive": True,
    "StandardOutPath": str(pathlib.Path(os.environ["MPT_AGENT_LOG_DIR"]) / "public-gateway.out.log"),
    "StandardErrorPath": str(pathlib.Path(os.environ["MPT_AGENT_LOG_DIR"]) / "public-gateway.err.log"),
}
with pathlib.Path(os.environ["MPT_AGENT_PLIST"]).open("wb") as stream:
    plistlib.dump(data, stream)
PY

uid="$(id -u)"
launchctl bootout "gui/$uid/$label" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$uid" "$plist"
launchctl enable "gui/$uid/$label"
launchctl kickstart -k "gui/$uid/$label"

gateway_status=""
for _ in 1 2 3 4 5; do
  gateway_status="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://127.0.0.1:8502/ 2>/dev/null || true)"
  [ "$gateway_status" = 401 ] && break
  sleep 1
done
if [ "$gateway_status" != 401 ]; then
  echo "公開ゲートウェイの認証拒否を確認できません。Funnelは開始していません。" >&2
  exit 1
fi

"$tailscale_cli" funnel --bg --https=8443 http://127.0.0.1:8502
dns_name="$("$tailscale_cli" status --json | "$python" -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')"
MPT_LINK_FILE="$link_file" MPT_LINK_KEY="$key_file" MPT_LINK_DNS="$dns_name" "$python" - <<'PY'
import os
import pathlib

key = pathlib.Path(os.environ["MPT_LINK_KEY"]).read_text(encoding="ascii").strip()
link = pathlib.Path(os.environ["MPT_LINK_FILE"])
link.write_text(f'https://{os.environ["MPT_LINK_DNS"]}:8443/?key={key}\n', encoding="ascii")
link.chmod(0o600)
PY
echo "iPhone/Windows用の専用リンクを保存しました: $link_file"
echo "このリンクを本人の端末へ転送し、最初に一度開いてください。次回からは公開URLをそのまま開けます。"
