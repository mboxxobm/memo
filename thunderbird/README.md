# Thunderbirdメールをローカルで整理するツール

Thunderbirdのプロファイルに保存されたメールを読み取り、Markdownへ書き出したり、新着メールや面談メールを整理したりするPythonスクリプトです。メールサーバーへ直接ログインせず、パスワードも使いません。

## メールをMarkdownに書き出す

```sh
python3 thunderbird_to_markdown.py --output "$HOME/Documents/Thunderbird-Markdown"
```

プロファイルの場所は自動で探します。必要なら `--profile` で指定できます。対象はThunderbirdがローカルに保存したメールです。IMAPの全フォルダーを扱うには、Thunderbirdの「同期とディスク領域」で必要なフォルダーを同期してください。

本文はMarkdownに含まれ、添付ファイルは名前のみ記録されます。

## 全アカウントの受信箱を監視する

```sh
python3 watch_thunderbird_inbox.py \
  --all-accounts --output "$HOME/Documents/Thunderbird-Markdown" \
  --interval 43200 --notify
```

起動時にローカル受信箱が見つかったアカウントを監視します。受信箱がないアドレスは表示されます。初回は既存メールを記録し、その後の新着だけをMarkdownに保存します。`43200` は12時間ごとの確認です。通知を続ける間は、PCを起動しThunderbirdの同期とターミナルを動作させてください。終了は `Ctrl+C` です。

アドレスを指定して監視する場合:

```sh
python3 watch_thunderbird_inbox.py \
  --accounts "name@example.com,other@example.com" \
  --interval 43200 --notify
```

## 面談・予約メールを探す

```sh
python3 summarize_meetings.py \
  --accounts "name@example.com,other@example.com" \
  --output "$HOME/Documents/Thunderbird-Markdown/面談一覧.md"
```

## 保存とプライバシー

Markdownにはメール本文が入ります。保存先とバックアップを適切に管理してください。Markdownを共有・アップロードすると、その本文も共有先へ送られます。メールデータ、Thunderbirdプロファイル、パスワードをGitHubに登録しないでください。
