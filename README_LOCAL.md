# MoneyPrinterTurbo ローカル運用メモ

- **導入/更新**: macOS・Linux `bash scripts/install.sh` → `~/mpt`／Windows `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` → `C:\mpt`。互換性確認済みの公式 `mpt==1.3.8` を専用venvへ導入します。
- **AI生成**: ローカル版は `Codex app server (ChatGPT login)` を既定のLLMとして設定します。事前に [Codex CLI](https://learn.chatgpt.com/docs/app-server) を導入して `codex login` を完了してください。動画の台本、素材検索語、投稿文案の生成時に、ログイン済みのCodex app serverへ接続します。モデル名を空欄にすると、app serverが示す既定モデルを選びます。Codexの利用枠が適用されます。
- **起動**: macOS `~/Applications/MoneyPrinterTurbo.app`（Dockに置く）／Windows デスクトップの `MoneyPrinterTurbo`（タスクバーにピン留め可）→ http://127.0.0.1:8501 。黒い窓を閉じると停止
- **データ**: `~/mpt/home`（Win: `C:\mpt\home`）= `MPT_HOME`。設定 `config.toml`、生成動画 `storage/tasks/<task-id>/final-1.mp4`
- **素材と音声**: WebUI「Settings」で Pexels キーを入力。音声 Edge TTS（`azure-tts-v1`）・字幕 `edge` は既定のままでキー不要。Codexはテキスト生成を担当し、素材取得・音声・動画合成には既存の仕組みを使います。
- **別端末からの利用（任意）**: Macでアプリを起動し、Macと利用端末を同じTailscaleネットワークに接続してから `bash scripts/serve-private.sh`。表示されたHTTPS URLをその端末で開きます。スクリプトを止めると共有も止まります。Tailscale Funnelは使いません。利用者のアクセス権はTailscale側で管理してください。
- **Render**: 現行のRender版は従来のLLM設定を使用し、ローカル版のCodexログインを共有しません。無料枠での動画生成はメモリ不足です。構成と代替案は [ホスティング検証](docs/hosting-options.md) を参照してください。
- **注意**: 同梱BGM `home/resource/songs` はYouTube由来。公開・業務用途では差し替える
