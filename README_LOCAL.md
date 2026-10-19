# MoneyPrinterTurbo ローカル運用メモ

- **導入/更新**: macOS・Linux `bash scripts/install.sh` → `~/mpt`／Windows `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` → `C:\mpt`（公式 `mpt` を専用venvへ。再実行で最新版に更新）
- **起動**: macOS `~/Applications/MoneyPrinterTurbo.app`（Dockに置く）／Windows デスクトップの `MoneyPrinterTurbo`（タスクバーにピン留め可）→ http://127.0.0.1:8501 。黒い窓を閉じると停止
- **データ**: `~/mpt/home`（Win: `C:\mpt\home`）= `MPT_HOME`。設定 `config.toml`、生成動画 `storage/tasks/<task-id>/final-1.mp4`
- **無料構成**: WebUI「Settings」で LLM（例: Gemini の無料キー）と Pexels キーを本人が入力。音声 Edge TTS（`azure-tts-v1`）・字幕 `edge` は既定のままでキー不要
- **注意**: 同梱BGM `home/resource/songs` はYouTube由来。公開・業務用途では差し替える
