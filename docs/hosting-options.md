# RenderとCodex app serverの運用判断（2026-10-20）

## 確認したこと

- Render公式の無料Webサービスは **0.1 CPU / 512 MB RAM**。15分無通信で停止し、停止・再起動・再デプロイでローカルの生成ファイルは失われる。無料枠には永続ディスクもない。現在の公開サービス `/healthz` は2026-10-20に HTTP 200 を返したが、これだけでは動画生成成功や契約プランは確認できない。Renderのプラン・メトリクス画面には今回アクセスできなかった。
- `HANDOFF.md` には従来の30秒・1080×1920動画の測定値として、待機時約260MB、`ultrafast` でも動画生成時約540MB（WebUI分は別）と記録されている。この数値は今回再測定していない。測定値の最小でも無料枠の512MBを超えるため、現行のモノリス構成では生成を無料枠に収められない。
- Renderの `1c-2g`（旧Standard）は1 CPU / 2 GB RAM。現行のRender Docker版にCodex app serverは同梱していないため、プラン変更だけではCodex連携に移行しない。
- OpenAIのChatGPTプランを使ったCodex連携は、現時点の公式案内ではローカルで動くオープンソース／個人プロジェクト向け。リモートホスト型で提供する場合は利用申請が必要。MacのCodexログインファイルをRenderに複製しない。

## 採用: Macで生成し、Tailscale経由でプライベートに遠隔利用

1. `bash scripts/install.sh` で `~/mpt` に導入し、Codex CLIでログインする。
2. `~/Applications/MoneyPrinterTurbo.app` でWebUIを起動する。WebUIは `127.0.0.1:8501` にだけバインドする。Mac側で動画生成し、動画と設定を `~/mpt/home` に保存する。
3. 常時利用するMac miniでは `bash scripts/install-macos-launchagent.sh` でWebUIをログイン時に自動起動し、`tailscale serve --bg --https=443 http://127.0.0.1:8501` でtailnet内にHTTPS転送する。`--bg` はTailscale再起動後も転送を再開する。
4. WindowsまたはiPhoneを同じtailnetに接続し、Mac miniのTailscale HTTPS URLを開く。Mac miniがスリープすると遠隔利用は止まる。今回のMac miniはAC電源時のシステムスリープが無効だが、電源断・ログアウト時の利用は保証しない。

このMacにはTailscale公式パッケージを導入し、本人のtailnetへの接続を確認した。Tailscale Serveは有効化済みで、このMacからtailnet内HTTPS経由の応答を確認した。Windows・iPhone実機からの接続試験は未実施。個人向け無料プランは非商用利用向けなので、業務利用する場合は契約条件を確認する。

### このMacでの受入結果（2026-10-20）

- `~/mpt` と `~/Applications/MoneyPrinterTurbo.app` を導入し、`config.toml` のプロバイダーが `codex_app_server` であることを確認した。
- WebUIは `127.0.0.1:8501` のみで待ち受け、`/` と `/_stcore/health` はHTTP 200だった。ただし、この応答だけではStreamlitの画面描画成功は確認できない。
- Codexの制限付きプロセスから起動したWebUIは、初回描画時に `~/mpt/home/resource` の作成が拒否された。制限のないMacのユーザー権限で再起動し、同じ資源配置処理で37ファイルの作成を確認した。再読み込み後の画面表示は利用者の確認待ち。
- Codex app serverへの短い生成と、`mpt cli --stop-at script` の台本生成が成功した。
- ローカル素材・音声を使った3秒の1080×1920 MP4を生成し、映像とAAC音声を検証した。検証ファイルは `/private/tmp/mpt-codex-acceptance` に置き、利用者の動画保存先には加えていない。
- Tailscale公式インストーラーの署名とSHA-256を確認して導入した。CLIの `tailscale status` でこのMacの接続を確認した。
- WebUIの日本語訳603件を導入し、既定言語を日本語に設定した。更新前から開いていた英語タブが再接続時に英語選択を再保存する問題は、保存済み言語を初回描画時に反映するパッチで修正した。
- `launchctl` でWebUIの自動起動とローカル待ち受けを確認した。`tailscale serve --bg` でプライベートHTTPS転送を常駐させ、`tailscale serve status --json` でローカルWebUIへの転送を確認した。以前の接続試験ではtailnet内HTTPS URLの `/_stcore/health` がHTTP 200を返した。Windows端末からの接続は未確認。

## 公開URLが必須の場合

Renderでの動画生成には少なくとも2GB級プランを候補とし、実動画でメモリ・時間・出力を測定する。素材取得用キー、LLM認証、永続保存（または生成直後のダウンロード）も必要。Codex app serverでChatGPTプランを使うにはリモートホスト向け利用資格と利用者認可を先に確認する。代わりにOpenAI API課金でCodexを認証する案は、別途APIキーと課金上限の設定が必要。現在のPRはRenderの認証やDockerに手を加えておらず、公開版はまだCodex移行済みではない。

## 根拠

- [Render Compute Plans](https://render.com/docs/compute-plans)
- [Render Free services](https://render.com/docs/free)
- [OpenAI Sign in with ChatGPTの利用範囲](https://learn.chatgpt.com/cookbook/articles/sign-in-with-chatgpt#usage-policy-and-terms)
- [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)
- [Tailscale pricing](https://tailscale.com/pricing)
