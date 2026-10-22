#!/usr/bin/env bash
# LaunchAgent entrypoint. Keep the access key out of plist files and command arguments.
set -euo pipefail

mpt_dir="${MPT_DIR:-$HOME/mpt}"
key_file="$mpt_dir/home/public-access.key"
if [ ! -r "$key_file" ]; then
  echo "公開アクセスキーがありません。install-macos-public-access.sh を実行してください。" >&2
  exit 1
fi
MPT_ACCESS_KEY="$(cat "$key_file")"
if [[ ! "$MPT_ACCESS_KEY" =~ ^[A-Za-z0-9_-]{16,}$ ]]; then
  echo "公開アクセスキーの形式が不正です。" >&2
  exit 1
fi
export MPT_ACCESS_KEY
export XDG_DATA_HOME="$mpt_dir/home/caddy-data"
export XDG_CONFIG_HOME="$mpt_dir/home/caddy-config"
exec "$mpt_dir/bin/caddy" run --config "$mpt_dir/Caddyfile.mac-public" --adapter caddyfile
