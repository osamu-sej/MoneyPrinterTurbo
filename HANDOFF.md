# 🔁 作業引き継ぎ｜MoneyPrinterTurbo ローカル導入＋Render公開｜2026-10-19

> この文書は2026-10-19時点の記録です。2026-10-22にMac miniのローカル版を公式 `mpt==1.3.9` へ更新し、Codex連携と日本語WebUIを確認しました。現在の導入手順と状態は [README_LOCAL.md](README_LOCAL.md) を参照してください。以下の版数・未実施事項は当時の情報です。

## ⚡受領指示（最初に読め）
これは作業の引き継ぎ。あなたは途中から再開する担当者。
- 経緯の説明・前提の再確認・「まず状況を整理すると…」の前置きは一切不要。
- 下の「次のTODO」から即着手する。
- 「動く資産」のコードは動作確認済み。再検証しない。
- 「地雷」のアプローチは二度と試さない。
- 質問は、着手をブロックするものだけ。それ以外は進めながら確認。
- このリポジトリは **public**。APIキー・アクセスキーは絶対にコミットしない。チャットにも貼らせない。

## 🎯 ゴール（1〜2行）
MoneyPrinterTurbo（題材→台本・素材・音声・字幕・BGM→短尺動画）を Render の公開URLとローカルの両方で使える状態にし、無料構成（Gemini＋Pexels＋Edge TTS）で1本生成を確認する。

## 📍 今ここ（1行）
Render に free プランでデプロイ・起動済み。動画の書き出しは 512MB で OOM になる見込みのため、本人によるカード登録→Standard 切替と APIキー登録待ち。ローカル導入はスクリプトのみで実機未実行。

## 📌 環境・確定制約
- repo `osamu-sej/MoneyPrinterTurbo`：全コードは `main`（PR #1〜#3 マージ済み）。GitHub の既定ブランチはまだ `claude/lucid-wright-09s5m7`
- アプリ本体は公式 PyPI `mpt==1.3.8`（PyPI の `MoneyPrinterTurbo` は第三者製）。WebUI に日本語表示なし
- Render：service `moneyprinterturbo`（`srv-dbb7uc2jnfac738bl02g`、workspace `tea-d58srcili9vc73a92jog`）、singapore、Docker、`main` へのコミットで自動デプロイ、URL https://moneyprinterturbo-he71.onrender.com
- 入場：`/?key=<MPT_ACCESS_KEY>` を一度開くと Cookie（1年）。キーの値は Render の Environment にだけある
- Render の環境変数：設定済み `MPT_ACCESS_KEY` `LLM_PROVIDER=gemini` `LLM_MODEL=gemini-3.5-flash-lite`／未設定 `LLM_API_KEY` `PEXELS_API_KEY`（起動時に `deploy/seed_config.py` が config.toml へ書き込む。ディスクは再起動で消える）
- 構成：Caddy（`$PORT`、`/healthz` 以外はキー必須）→ Streamlit 127.0.0.1:8501。ffmpeg は `IMAGEIO_FFMPEG_EXE` 経由のラッパー（`X264_PRESET`、既定 veryfast）
- メモリ・時間の実測（1CPU、30秒・1080×1920）：待機時 約260MB／生成時ピーク medium 940MB・veryfast 740MB・ultrafast 540MB（WebUI 分は別）→ **2GB（Standard）が必須**
- ローカル：`scripts/install.sh` → `~/mpt`（mac は `~/Applications/MoneyPrinterTurbo.app` も作る）、`scripts/install.ps1` → `C:\mpt`＋デスクトップショートカット。`MPT_HOME=<導入先>/home`
- Claude のクラウド作業環境からは `onrender.com`・Edge TTS・Pexels・`deb.debian.org` に接続できない。Render の確認は Render MCP（`list_events` / `list_logs` / `get_metrics`）で行う

## ✅ 動く資産（コピペで動く確定版のみ）
```bash
# ローカル導入・更新（再実行で mpt を最新版に）
bash scripts/install.sh                                            # macOS / Linux
powershell -ExecutionPolicy Bypass -File scripts\install.ps1       # Windows

# キー不要の合成テスト（台本を直接渡す＋ローカル素材＋手元の音声）
MPT_HOME=~/mpt/home ~/mpt/.venv/bin/mpt cli \
  --video-script "テスト用の台本です。" --video-source local \
  --video-materials a.mp4,b.mp4 --custom-audio-file voice.mp3 --no-subtitle-enabled
# → ~/mpt/home/storage/tasks/<task-id>/final-1.mp4
```

## ❌ 地雷（再試行禁止｜結論だけ）
- Render の free / starter（512MB）で動画生成 → OOM。ffmpeg 2本の同時実行で約1GB必要。threads=1 にしても減らない
- Render MCP で有料プランのサービスを作る → 402（支払い情報が未登録）
- Vercel Sandbox → プロジェクトが0件で、作成も 403 のため使えない
- 公式 caddy イメージのバイナリをそのまま COPY → Render で exit 126「Operation not permitted」（ファイルケーパビリティが原因）。caddy ステージ内で `cp` してから COPY する
- Caddyfile の `redir / 302` → `/` がマッチャー扱いになり `Location: 302`。正しくは `redir * / 302`
- Basic 認証 → Safari が Streamlit の WebSocket に認証情報を送らない。Cookie 方式にする
- `IMAGEIO_FFMPEG_EXE` を設定した後に `imageio_ffmpeg.get_ffmpeg_exe()` → ラッパー自身が返り再帰する。先に `env -u` で実体のパスを解決する
- `mpt cli --task-id` は UUID 以外を受け付けない
- Windows で日本語や空白を含むパスに導入 → 動作不良。ASCII のみ
- 同梱 BGM（`resource/songs`）は YouTube 由来 → 公開・業務用途では差し替える

## ▶ 次のTODO（ここから着手）
1. （本人）https://dashboard.render.com/billing でカード登録 → サービスの Settings → Instance Type を **Standard** に変更
2. （本人）Render の Environment に `LLM_API_KEY`（https://aistudio.google.com/app/apikey）と `PEXELS_API_KEY` を追加（保存すると自動で再デプロイ）
3. `URL/?key=...` で開き、短い題材で1本生成してダウンロードまで確認。失敗したら `list_logs`・`list_events`（OOM は server_failed）・`get_metrics`（memory_usage）で原因を見る
4. ローカルでも使う場合：実機で install スクリプトを実行し、アプリ／ショートカットからの起動と1本生成を確認（mac の `.app` 作成と `install.ps1` は実機未検証）
5. （本人）GitHub の Settings → General → Default branch を `main` に変更

## ❓ 未決（着手をブロックするものだけ）
- Render を有料（Standard、月額約25ドル・日割り）にするか、ローカル運用だけにするか（本人の判断。TODO 1〜3 はこれ次第）
