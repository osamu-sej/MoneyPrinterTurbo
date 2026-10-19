# MoneyPrinterTurbo ローカル運用メモ

- **導入/更新**: macOS・Linux `bash scripts/install.sh` → `~/mpt`／Windows `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` → `C:\mpt`（公式 `mpt` を専用venvへ。再実行で最新版に更新）
- **起動**: macOS `~/Applications/MoneyPrinterTurbo.app`（Dockに置く）／Windows デスクトップの `MoneyPrinterTurbo`（タスクバーにピン留め可）→ http://127.0.0.1:8501 。黒い窓を閉じると停止
- **データ**: `~/mpt/home`（Win: `C:\mpt\home`）= `MPT_HOME`。設定 `config.toml`、生成動画 `storage/tasks/<task-id>/final-1.mp4`
- **無料構成**: WebUI「Settings」で LLM（例: Gemini の無料キー）と Pexels キーを本人が入力。音声 Edge TTS（`azure-tts-v1`）・字幕 `edge` は既定のままでキー不要
- **クラウド**: Render（`Dockerfile`、Standard 2GB。512MB プランは生成時に OOM）。`https://<サービス>.onrender.com/?key=<MPT_ACCESS_KEY>` を一度開くと入れる。キーは Render の Environment に `LLM_API_KEY` `PEXELS_API_KEY`（任意: `LLM_PROVIDER` `LLM_MODEL` `PIXABAY_API_KEY` `MPT_VOICE_NAME` `X264_PRESET`）。ディスクは再起動で消えるので動画はその場でDL
- **注意**: 同梱BGM `home/resource/songs` はYouTube由来。公開・業務用途では差し替える
