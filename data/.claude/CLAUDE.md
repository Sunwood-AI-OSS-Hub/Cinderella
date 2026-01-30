# Cinderella プロジェクト

## 基本方針

- **sudo**: パスワードなしで使用可能
- **パッケージ**: 必要に応じてインストール
- **役割**: マネージャーとして全体を俯瞰し、サブエージェントを活用

## 開発方針

1. 全体像を把握してから取り組む
2. サブエージェントに具体的な作業を任せる
3. 進捗を確認しながら適宜ガイド

---

## Discord ファイル添付ワークフロー

### 📥 受信（Discord → Cinderella）

1. **自動保存**: Discordに添付されたファイルは自動的に `/workspace/media/` に保存されます
   - ファイル名: `YYYYMMDD_HHMMSS_元のファイル名`
   - 保存先: `/workspace/media`

2. **通知メッセージ**: Botから以下の通知が送信されます
   ```
   📁 添付ファイルを保存しました
   ⏰ 2026-01-29 23:06:23
   👤 送信者: Maki
   📂 保存先: `/workspace/media`

   1. v2_mkz7p1lhb11526ea9bc8a2d8.jpg_.webp
      - ファイルパス: `/workspace/media/20260129_230623_v2_mkz7p1lh_b11526ea9bc8a2d8.jpg_.webp`
      - サイズ: 129.31 KB
   ```

3. **チャット履歴**: 通知メッセージはチャット履歴に含まれるので、エージェントはファイルパスを認識できます

### 📤 送信（Cinderella → Discord）

`/discord` スキルを使ってファイルを送信できます：

```json
{
  "action": "sendFile",
  "channelId": "1466415185282732220",
  "filePath": "/workspace/media/sample.png",
  "content": "画像を生成しました"
}
```

**サポートされているファイル形式:**
- 画像: PNG, JPG, JPEG, WEBP, GIF など
- 動画: MP4, WEBM, MOV など
- ドキュメント: PDF, TXT, MD など

## よく使うコマンド例

### 画像を分析して送信

```bash
# 画像を分析（agentic-vision-gemini スキル）
/agentic-vision-gemini

# 画像を加工して保存
convert /workspace/media/input.jpg -gravity center -crop 50%x50% /workspace/media/cropped.png

# Discordに送信
/discord
```

### PDFを解析して送信

```bash
# PDFのテキストを抽出
pdftotext /workspace/media/document.pdf -

# 結果をDiscordに送信
/discord
```

## ファイルパスについて

- **保存先**: `/workspace/media`
- **Claude Codeからアクセス可能**: `/workspace/media/filename.ext`
- **discord-botコンテナ内部**: `/workspace/media` （同じパス）

## 注意事項

- ファイルは自動的に上書きされません（タイムスタンプで一意）
- 大きなファイルはアップロードに時間がかかる場合があります
- Discordのファイルサイズ制限（最大25MB）に注意してください
