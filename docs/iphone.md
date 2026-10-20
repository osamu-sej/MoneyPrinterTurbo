# iPhoneからMoneyPrinterTurboを使う

1. iPhoneへ[公式Tailscaleアプリ](https://tailscale.com/docs/install/ios)を入れます。初回のVPN構成を許可し、Mac miniと同じGitHubアカウントでログインして、Tailscaleを接続します。
2. Safariで [MoneyPrinterTurbo](https://mac-mini.tail347817.ts.net/) を開きます。自宅のWi-Fiを切ってモバイル通信でも開ければ、外出先からの接続を確認できます。
3. よく使う場合はSafariの共有メニューから「ホーム画面に追加」を選びます。操作は[Appleの手順](https://support.apple.com/ja-jp/guide/iphone/iphea86e5236/ios)を参照してください。

Mac miniは電源を入れ、ユーザーがログインした状態にしておきます。画面が開かない場合は、iPhoneのTailscaleが接続中で、Mac miniと同じtailnetにいることを先に確認してください。このURLはtailnet内だけで利用できます。

Mac mini側はTailscale Serveをバックグラウンドで起動済みです。iPhone本体でのSafari表示と動画のダウンロードは、iPhoneをtailnetへ接続してから確認します。
