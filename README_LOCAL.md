# MoneyPrinterTurbo ローカル運用メモ

- **導入/更新**: macOS・Linux `bash scripts/install.sh` → `~/mpt`／Windows `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` → `C:\mpt`。互換性確認済みの公式 `mpt==1.3.8` を専用venvへ導入します。
- **AI生成**: ローカル版は `Codex app server (ChatGPT login)` を既定のLLMとして設定します。事前に [Codex CLI](https://learn.chatgpt.com/docs/app-server) を導入して `codex login` を完了してください。動画の台本、素材検索語、投稿文案の生成時に、ログイン済みのCodex app serverへ接続します。モデル名を空欄にすると、app serverが示す既定モデルを選びます。Codexの利用枠が適用されます。
- **起動**: macOS `~/Applications/MoneyPrinterTurbo.app`（Dockに置く）／Windows デスクトップの `MoneyPrinterTurbo`（タスクバーにピン留め可）→ http://127.0.0.1:8501 。黒い窓を閉じると停止
- **データ**: `~/mpt/home`（Win: `C:\mpt\home`）= `MPT_HOME`。設定 `config.toml`、生成動画 `storage/tasks/<task-id>/final-1.mp4`
- **素材と音声**: WebUI「Settings」で Pexels キーを入力。音声 Edge TTS（`azure-tts-v1`）・字幕 `edge` は既定のままでキー不要。Codexはテキスト生成を担当し、素材取得・音声・動画合成には既存の仕組みを使います。
- **クラウド**: Render（`Dockerfile`、Standard 2GB。512MB プランは生成時に OOM）。`https://<サービス>.onrender.com/?key=<MPT_ACCESS_KEY>` を一度開くと入れる。キーはRenderのEnvironmentに `LLM_API_KEY` `PEXELS_API_KEY`（任意: `LLM_PROVIDER` `LLM_MODEL` `PIXABAY_API_KEY` `MPT_VOICE_NAME` `X264_PRESET`）。現行のRender版は従来のLLM設定を使用し、ローカル版のCodexログインを共有しません。ホスト型サービスでChatGPTプランを使うには、[OpenAIの「Sign in with ChatGPT」](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)による利用者の認可とトークン更新が必要です。ディスクは再起動で消えるので動画はその場でDL
- **注意**: 同梱BGM `home/resource/songs` はYouTube由来。公開・業務用途では差し替える
