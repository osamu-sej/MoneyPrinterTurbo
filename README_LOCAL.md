# MoneyPrinterTurbo ローカル運用メモ

- **導入/更新**: macOS・Linux `bash scripts/install.sh` → `~/mpt`／Windows `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` → `C:\mpt`。互換性確認済みの公式 `mpt==1.3.8` を専用venvへ導入し、画面を日本語に設定します。
- **AI生成**: ローカル版は `Codex app server (ChatGPT login)` を既定のLLMとして設定します。事前に [Codex CLI](https://learn.chatgpt.com/docs/app-server) を導入して `codex login` を完了してください。動画の台本、素材検索語、投稿文案の生成時に、ログイン済みのCodex app serverへ接続します。モデル名を空欄にすると、app serverが示す既定モデルを選びます。Codexの利用枠が適用されます。
- **手動起動**: macOS `~/Applications/MoneyPrinterTurbo.app`（Dockに置く）／Windows デスクトップの `MoneyPrinterTurbo`（タスクバーにピン留め可）→ http://127.0.0.1:8501 。手動起動したターミナルを閉じると停止
- **データ**: `~/mpt/home`（Win: `C:\mpt\home`）= `MPT_HOME`。設定 `config.toml`、生成動画 `storage/tasks/<task-id>/final-1.mp4`
- **素材と音声**: WebUI「設定」で Pexels キーを入力。音声 Edge TTS（`azure-tts-v1`）・字幕 `edge` は既定のままでキー不要。Codexはテキスト生成を担当し、素材取得・音声・動画合成には既存の仕組みを使います。
- **外出先から使うMac miniの設定**: `bash scripts/install-macos-launchagent.sh` でWebUIをログイン時に自動起動します。Tailscaleに接続後、`tailscale serve --bg --https=443 http://127.0.0.1:8501` でtailnet内だけにHTTPS公開します。`--bg` は再起動後もServeを再開します。停止する場合は `tailscale serve --https=443 off` を使用します。Funnelは使いません。
- **Windowsからの利用**: Windowsに[公式Tailscale](https://tailscale.com/docs/install/windows)を導入し、Mac miniと同じアカウントでログインします。接続後、`https://mac-mini.tail347817.ts.net/` をブラウザで開きます。Mac miniが起動・ログインしている必要があります。アクセス権はTailscale側で管理します。
- **既存の英語タブ**: 更新前から開いているタブは、再接続時に英語設定を保存し直す場合があります。画面右上の言語メニューで「日本語」を一度選択すると、以降の表示言語として保存されます。
- **一時的な共有**: 自動起動を設定しない場合、Macでアプリを起動して `bash ~/mpt/serve-private.sh` を実行します。ターミナルを閉じると共有が止まります。
- **Render**: 現行のRender版は従来のLLM設定を使用し、ローカル版のCodexログインを共有しません。無料枠での動画生成はメモリ不足です。構成と代替案は [ホスティング検証](docs/hosting-options.md) を参照してください。
- **注意**: 同梱BGM `home/resource/songs` はYouTube由来。公開・業務用途では差し替える
