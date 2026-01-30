---
name: discord
description: Use when you need to control Discord from Cinderella via the discord tool: send messages, react, edit/delete messages, manage threads/pins, fetch member/role/channel/emoji info, read messages, or check permissions in Discord channels.
metadata: {"cinderella":{"emoji":"💬","endpoint":"http://discord-bot:8080/v1/discord/action","endpoint_local":"http://localhost:8082/v1/discord/action"}}
---

# Discord Actions for Cinderella

## Overview

Use `discord` to manage Discord operations from Claude Code via Cinderella's local API. The API is compatible with Moltbot's format and runs on `http://discord-bot:8080/v1/discord/action` from within containers.

## Supported Actions

All actions are executed via curl to the local API endpoint:

```bash
curl -s http://discord-bot:8080/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"action":"...","...":"..."}'
```

## Inputs to collect

- For reactions: `channelId`, `messageId`, and an `emoji`.
- For fetchMessage: `guildId`, `channelId`, and `messageId`.
- For sendMessage: `channelId` and `content`. Optional: `replyTo` for replying to a specific message.
- For threads: `channelId`, optional `messageId` (for create), `threadId` (for reply), or `guildId` (for list).
- For member info: `guildId` and `userId`.
- For role/emoji/channel info: `guildId` or `channelId`.

## Actions

### React to a message

```json
{
  "action": "react",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "emoji": "✅"
}
```

**Response:**
```json
{"success": true, "data": {"message": "Reaction added"}}
```

### List reactions on a message

```json
{
  "action": "reactions",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "limit": 100
}
```

**Response:**
```json
{
  "success": true,
  "data": {"reactions": [{"emoji": {"name": "✅"}, "count": 1}], "count": 1}
}
```

### Send a message

```json
{
  "action": "sendMessage",
  "channelId": "1234567890",
  "content": "Hello from Claude Code!"
}
```

**Response:**
```json
{"success": true, "data": {"message_id": "123456789012345678"}}
```

### Send a reply message

特定のメッセージに返信（リプライ）として送信します。

```json
{
  "action": "sendMessage",
  "channelId": "1234567890",
  "content": "This is a reply message!",
  "replyTo": "0987654321"
}
```

**Response:**
```json
{"success": true, "data": {"message_id": "123456789012345679"}}
```

### Send a file (画像、動画、ドキュメントなど)

ファイルを添付して送信します。画像、動画、PDFなどのファイルをDiscordに投稿できます。

```json
{
  "action": "sendFile",
  "channelId": "1234567890",
  "filePath": "/workspace/media/sample.png",
  "content": "画像を生成しました"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id": "123456789012345678",
    "file_name": "sample.png",
    "file_path": "/workspace/media/sample.png"
  }
}
```

**サポートされているファイル形式:**
- 画像: PNG, JPG, JPEG, WEBP, GIF など
- 動画: MP4, WEBM, MOV など
- ドキュメント: PDF, TXT, MD など

**ファイルパスについて:**
- ファイルは `/workspace/media` ディレクトリに保存してください
- Discordに添付されたファイルは自動的に `/workspace/media` に保存されます
- ファイル名はタイムスタンプ付きで自動保存されます（例: `20260129_230212_filename.jpg`）

## Debate Functionality

The Discord bot supports bot-to-bot debates through the `!debate` command.

### Starting a debate

Users can initiate a debate using:

```
!debate <トピック> [--personality=<type>]
```

**Available personalities:**
- `optimist` - 楽観派AI (positive/constructive)
- `pessimist` - 慎重派AI (careful/critical)
- `neutral` - 中立派AI (objective/balanced)

**Examples:**
```
!debate AIと仕事
!debate リモートワークの是非 --personality=optimist
!debate 気候変動対策 --personality=pessimist
```

### How it works

1. When `!debate` is used, the bot starts a debate context for that channel
2. The bot responds to the topic using its assigned personality
3. Other bots in the channel can participate by responding to messages
4. The debate automatically concludes after 5 turns per bot or when consensus is reached
5. A summary message is posted when the debate ends

### Debate behavior

- Bots only respond to other bots' messages during debates
- Each bot has a personality that influences their responses
- The debate context is channel-specific
- Debates automatically end to prevent infinite loops
- Summary keywords trigger conclusion: "まとめ", "ご清聴", "結論", "終了"

### Edit a message

```json
{
  "action": "editMessage",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "content": "Updated message content"
}
```

**Response:**
```json
{"success": true, "data": {"message": "Message edited"}}
```

### Delete a message

```json
{
  "action": "deleteMessage",
  "channelId": "1234567890",
  "messageId": "0987654321"
}
```

**Response:**
```json
{"success": true, "data": {"message": "Message deleted"}}
```

### Read recent messages

```json
{
  "action": "readMessages",
  "channelId": "1234567890",
  "limit": 20
}
```

**Response:**
```json
{
  "success": true,
  "data": {"messages": [...], "count": 20}
}
```

### Fetch a single message

```json
{
  "action": "fetchMessage",
  "guildId": "1188045372526964796",
  "channelId": "1234567890",
  "messageId": "0987654321"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"id": "...", "content": "...", "author": {...}}
}
```

### Create a thread

```json
{
  "action": "threadCreate",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "name": "Discussion thread"
}
```

**Response:**
```json
{"success": true, "data": {"thread_id": "123456789012345678"}}
```

### List threads in a guild

```json
{
  "action": "threadList",
  "guildId": "1188045372526964796"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"threads": [...], "count": 5}
}
```

### Reply to a thread

```json
{
  "action": "threadReply",
  "threadId": "123456789012345678",
  "content": "Replying in the thread"
}
```

**Response:**
```json
{"success": true, "data": {"message_id": "123456789012345678"}}
```

### Pin a message

```json
{
  "action": "pinMessage",
  "channelId": "1234567890",
  "messageId": "0987654321"
}
```

**Response:**
```json
{"success": true, "data": {"message": "Message pinned"}}
```

### List pinned messages

```json
{
  "action": "listPins",
  "channelId": "1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"pins": [...], "count": 3}
}
```

### Get member information

```json
{
  "action": "memberInfo",
  "guildId": "1188045372526964796",
  "userId": "539207222494699520"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"username": "...", "display_name": "...", "roles": [...]}
}
```

### Get role information

```json
{
  "action": "roleInfo",
  "guildId": "1188045372526964796"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"roles": [...], "count": 10}
}
```

### List custom emojis

```json
{
  "action": "emojiList",
  "guildId": "1188045372526964796"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"emojis": [...], "count": 25}
}
```

### Get channel information

```json
{
  "action": "channelInfo",
  "channelId": "1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"id": "...", "name": "...", "type": 0, "topic": "..."}
}
```

### List channels in a guild

```json
{
  "action": "channelList",
  "guildId": "1188045372526964796"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"channels": [...], "count": 15}
}
```

### Check bot permissions

```json
{
  "action": "permissions",
  "channelId": "1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "data": {"permissions": {"send_messages": true, ...}}
}
```

## Ideas to try

- React with ✅/⚠️ to mark status updates.
- Create threads for discussions from important messages.
- Pin important announcements or decisions.
- Send notifications from long-running CLI tasks.
- Check member info for verification.
- List channels to find the right place to post.
- **Send generated images/files to Discord** - Use `sendFile` to share your creations with the channel.
- **Process attachments** - Files attached to Discord are automatically saved to `/workspace/media` for you to analyze.

## Error handling

All actions return a consistent response format:

**Success:**
```json
{"success": true, "data": {...}}
```

**Error:**
```json
{"success": false, "error": "Error message"}
```

## Discord Writing Style Guide

**Keep it conversational!** Discord is a chat platform, not documentation.

### Do
- Short, punchy messages (1-3 sentences ideal)
- Multiple quick replies > one wall of text
- Use emoji for tone/emphasis 🦞
- Lowercase casual style is fine
- Break up info into digestible chunks
- Match the energy of the conversation

### Don't
- No markdown tables (Discord renders them as ugly raw `| text |`)
- No `## Headers` for casual chat (use **bold** or CAPS for emphasis)
- Avoid multi-paragraph essays
- Don't over-explain simple things
- Skip the "I'd be happy to help!" fluff

### Formatting that works
- **bold** for emphasis
- `code` for technical terms
- Lists for multiple items
- > quotes for referencing
- Wrap multiple links in `<>` to suppress embeds

### Example transformations

❌ Bad:
```
I'd be happy to help with that! Here's a comprehensive overview of the versioning strategies available:

## Semantic Versioning
Semver uses MAJOR.MINOR.PATCH format where...

## Calendar Versioning
CalVer uses date-based versions like...
```

✅ Good:
```
versioning options: semver (1.2.3), calver (2026.01.04), or yolo (`latest` forever). what fits your release cadence?
```
