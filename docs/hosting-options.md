# RenderとCodex app serverの運用判断（2026-10-20）

## 確認したこと

- Render公式の無料Webサービスは **0.1 CPU / 512 MB RAM**。15分無通信で停止し、停止・再起動・再デプロイでローカルの生成ファイルは失われる。無料枠には永続ディスクもない。現在の公開サービス `/healthz` は2026-10-20に HTTP 200 を返したが、これだけでは動画生成成功や契約プランは確認できない。Renderのプラン・メトリクス画面には今回アクセスできなかった。
- `HANDOFF.md` には従来の30秒・1080×1920動画の測定値として、待機時約260MB、`ultrafast` でも動画生成時約540MB（WebUI分は別）と記録されている。この数値は今回再測定していない。測定値の最小でも無料枠の512MBを超えるため、現行のモノリス構成では生成を無料枠に収められない。
- Renderの `1c-2g`（旧Standard）は1 CPU / 2 GB RAM。現行のRender Docker版にCodex app serverは同梱していないため、プラン変更だけではCodex連携に移行しない。
- OpenAIのChatGPTプランを使ったCodex連携は、現時点の公式案内ではローカルで動くオープンソース／個人プロジェクト向け。リモートホスト型で提供する場合は利用申請が必要。MacのCodexログインファイルをRenderに複製しない。

## 推奨: Macで生成、必要時だけプライベートに遠隔利用

1. `bash scripts/install.sh` で `~/mpt` に導入し、Codex CLIでログインする。
2. `~/Applications/MoneyPrinterTurbo.app` でWebUIを起動する。WebUIは `127.0.0.1:8501` にだけバインドする。Mac側で動画生成し、動画と設定を `~/mpt/home` に保存する。
3. 別端末から使う場合は、Macと利用端末を同じTailscaleネットワークに接続し、リポジトリから `bash scripts/serve-private.sh` を実行する。Tailscale ServeのHTTPS URLはネットワーク内の許可端末向け。共有中はWebUIのターミナルとServeのターミナルを開いておく。
4. 利用後はServe側を `Ctrl+C` で止める。Macをスリープさせると遠隔利用も止まる。

TailscaleはこのMacに未導入であり、実際の遠隔接続試験は未実施。個人向け無料プランは非商用利用向けなので、業務利用する場合は契約条件を確認する。

## 公開URLが必須の場合

Renderでの動画生成には少なくとも2GB級プランを候補とし、実動画でメモリ・時間・出力を測定する。素材取得用キー、LLM認証、永続保存（または生成直後のダウンロード）も必要。Codex app serverでChatGPTプランを使うにはリモートホスト向け利用資格と利用者認可を先に確認する。代わりにOpenAI API課金でCodexを認証する案は、別途APIキーと課金上限の設定が必要。現在のPRはRenderの認証やDockerに手を加えておらず、公開版はまだCodex移行済みではない。

## 根拠

- [Render Compute Plans](https://render.com/docs/compute-plans)
- [Render Free services](https://render.com/docs/free)
- [OpenAI Sign in with ChatGPTの利用範囲](https://learn.chatgpt.com/cookbook/articles/sign-in-with-chatgpt#usage-policy-and-terms)
- [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)
- [Tailscale pricing](https://tailscale.com/pricing)
