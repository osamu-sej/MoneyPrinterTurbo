# MoneyPrinterTurbo ローカル運用メモ

- **導入/更新**: macOS・Linux `bash scripts/install.sh` → `~/mpt`／Windows `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` → `C:\mpt`。互換性確認済みの公式 `mpt==1.3.8` を専用venvへ導入し、画面を日本語に設定します。
- **AI生成**: ローカル版は `Codex app server (ChatGPT login)` を既定のLLMとして設定します。事前に [Codex CLI](https://learn.chatgpt.com/docs/app-server) を導入して `codex login` を完了してください。動画の台本、素材検索語、投稿文案の生成時に、ログイン済みのCodex app serverへ接続します。モデル名を空欄にすると、app serverが示す既定モデルを選びます。Codexの利用枠が適用されます。
- **手動起動**: macOS `~/Applications/MoneyPrinterTurbo.app`（Dockに置く）／Windows デスクトップの `MoneyPrinterTurbo`（タスクバーにピン留め可）→ http://127.0.0.1:8501 。手動起動したターミナルを閉じると停止
- **データ**: `~/mpt/home`（Win: `C:\mpt\home`）= `MPT_HOME`。設定 `config.toml`、生成動画 `storage/tasks/<task-id>/final-1.mp4`
- **素材と音声**: WebUI「設定」で Pexels キーを入力。音声 Edge TTS（`azure-tts-v1`）・字幕 `edge` は既定のままでキー不要。Codexはテキスト生成を担当し、素材取得・音声・動画合成には既存の仕組みを使います。
- **生成前の確認**: 「動画を生成」の直前にCodexのログイン、選択中の主要素材サービスのAPIキー、ローカル素材の有無を表示します。不足時は「設定を開く」から入力でき、「接続を再確認」でCodexの状態を更新できます。
- **ローカル画像のサイズ**: 縦横とも480px以上の元画像を使ってください。小さな画像を選ぶと、生成前に実際の寸法を表示してボタンを無効にします。サムネイルの拡大では文字の判読性は改善しないため、元データをアップロードしてください。
- **外出先から使うMac miniの設定**: `bash scripts/install-macos-launchagent.sh` でWebUIをログイン時に自動起動します。続けて `bash scripts/install-macos-public-access.sh` で、専用リンクを一度開けば以後ログイン操作なく使えるHTTPS入口を設定します。公開側はMacのローカルゲートウェイで本人のCookieを確認し、Tailscale Funnelの8443番ポートへ転送します。既存のtailnet限定Serve（443番ポート）も維持します。停止する場合は `tailscale funnel --https=8443 off` を実行します。
- **Windowsからの利用**: Mac miniの `~/mpt/home/public-access-link.txt` に保存された専用リンクを本人のWindowsへ安全に転送し、ブラウザで最初に一度開きます。以後は `https://mac-mini.tail347817.ts.net:8443/` を開けます。WindowsへTailscaleを入れる必要はありません。Mac miniが起動・ログインしている必要があります。
- **iPhoneからの利用**: [iPhone向け手順](docs/iphone.md)に従い、Safariで専用リンクを一度開きます。iPhoneへTailscaleを入れる必要はありません。画面幅に応じて設定欄が縦に並びます。
- **表示言語**: 保存済みの言語をタブの再接続時にも反映し、AI・音声サービスの設定説明も日本語で表示します。画面右上の言語メニューで変更できます。
- **一時的な共有**: 自動起動を設定しない場合、Macでアプリを起動して `bash ~/mpt/serve-private.sh` を実行します。ターミナルを閉じると共有が止まります。
- **Render**: 現行のRender版は従来のLLM設定を使用し、ローカル版のCodexログインを共有しません。無料枠での動画生成はメモリ不足です。構成と代替案は [ホスティング検証](docs/hosting-options.md) を参照してください。
- **注意**: 同梱BGM `home/resource/songs` はYouTube由来。公開・業務用途では差し替える
