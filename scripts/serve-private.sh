#!/usr/bin/env bash
# Share the locally running WebUI only with devices allowed into this tailnet.
# Keep this terminal open while remote access is needed; Ctrl+C stops sharing.
set -euo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale CLI が見つかりません。先に公式クライアントを導入してください。" >&2
  exit 1
fi

if ! tailscale status >/dev/null 2>&1; then
  echo "Tailscale に接続してください。" >&2
  exit 1
fi

if ! curl -fsS --max-time 5 http://127.0.0.1:8501/_stcore/health >/dev/null; then
  echo "MoneyPrinterTurbo を先に起動してください (http://127.0.0.1:8501)。" >&2
  exit 1
fi

exec tailscale serve --https=443 http://127.0.0.1:8501
