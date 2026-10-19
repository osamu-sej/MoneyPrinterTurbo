#!/usr/bin/env bash
# MoneyPrinterTurbo（公式PyPIパッケージ mpt）を専用venvに導入し、起動ランチャーを作る（macOS / Linux）。
# Codex連携と互換のある mpt==1.3.8 に固定する。導入先は MPT_DIR で変更可（既定: ~/mpt）。
set -euo pipefail

MPT_DIR="${MPT_DIR:-$HOME/mpt}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 日本語・空白を含むパスは動作不良の原因になるため拒否する
if printf '%s' "$MPT_DIR" | LC_ALL=C grep -q '[^A-Za-z0-9/._-]'; then
  echo "導入先パスは ASCII（英数字 / . _ -）のみにしてください: $MPT_DIR" >&2
  echo "例: MPT_DIR=/Users/Shared/mpt bash $0" >&2
  exit 1
fi

find_python() {
  for c in python3.11 python3.12 python3.13 python3; do
    if command -v "$c" >/dev/null 2>&1 &&
      "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

if ! PY="$(find_python)"; then
  echo "Python 3.11 以上が見つかりません。macOS: brew install python@3.11 / https://www.python.org/downloads/" >&2
  exit 1
fi

mkdir -p "$MPT_DIR"
if [ ! -x "$MPT_DIR/.venv/bin/python" ]; then
  echo "venv を作成: $MPT_DIR/.venv（$("$PY" --version)）"
  "$PY" -m venv "$MPT_DIR/.venv"
fi
"$MPT_DIR/.venv/bin/python" -m pip install --upgrade pip 'mpt==1.3.8'
echo "導入済み: $("$MPT_DIR/.venv/bin/mpt" --version)"

mkdir -p "$MPT_DIR/codex_overlay"
cp -R "$REPO_DIR/codex_overlay/." "$MPT_DIR/codex_overlay/"
MPT_HOME="$MPT_DIR/home" PYTHONPATH="$MPT_DIR/codex_overlay" MPT_CODEX_APP_SERVER=1 \
  "$MPT_DIR/.venv/bin/python" -c \
  'from app.config import config; config.app["llm_provider"] = "codex_app_server"; config.save_config()'

# システムに ffmpeg が無くても、mpt 同梱の imageio-ffmpeg で動くことを確認する
"$MPT_DIR/.venv/bin/python" -c \
  'import imageio_ffmpeg, subprocess; subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-version"], check=True, capture_output=True)'

if [ "$(uname)" = Darwin ]; then
  LAUNCHER="$MPT_DIR/MoneyPrinterTurbo.command"
else
  LAUNCHER="$MPT_DIR/start.sh"
fi

# ランチャーはここで生成する（ダウンロードしたファイルをコピーすると macOS の検疫属性で起動を拒否されるため）
cat >"$LAUNCHER" <<'EOF'
#!/usr/bin/env bash
# MoneyPrinterTurbo を起動する。既に起動中ならブラウザで開くだけ。このウィンドウを閉じると停止する。
cd "$(dirname "$0")" || exit 1
export MPT_HOME="$PWD/home"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PYTHONPATH="$PWD/codex_overlay${PYTHONPATH:+:$PYTHONPATH}"
export MPT_CODEX_APP_SERVER=1
if ! command -v codex >/dev/null 2>&1; then
  echo "Codex CLI が見つかりません。Codex CLI を導入し、codex login を実行してください。" >&2
  exit 1
fi
URL="http://127.0.0.1:8501"
if curl -fsS "$URL/_stcore/health" >/dev/null 2>&1; then
  if [ "$(uname)" = Darwin ]; then open "$URL"; else xdg-open "$URL"; fi
  exit 0
fi
ulimit -n 10240 2>/dev/null || true
exec ./.venv/bin/mpt webui --host 127.0.0.1 --port 8501
EOF
chmod +x "$LAUNCHER"
echo "ランチャー: $LAUNCHER"

if [ "$(uname)" = Darwin ]; then
  APP_DIR="${MPT_APP_DIR:-$HOME/Applications}"
  APP="$APP_DIR/MoneyPrinterTurbo.app"
  mkdir -p "$APP_DIR"
  rm -rf "$APP"
  osacompile -o "$APP" -e "do shell script \"open '$LAUNCHER'\""
  echo "アプリ: ${APP}（Finder でこのアプリを Dock にドラッグすると常用できます）"
fi

echo "データ保存先（MPT_HOME）: $MPT_DIR/home  生成動画: $MPT_DIR/home/storage/tasks/<task-id>/"
