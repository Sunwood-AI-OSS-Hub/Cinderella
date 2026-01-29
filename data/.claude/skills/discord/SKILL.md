---
name: discord
description: Use when you need to control Discord from Cinderella via the discord tool: send messages, react, edit/delete messages, manage threads/pins, fetch member/role/channel/emoji info, read messages, or check permissions in Discord channels.
metadata: {"cinderella":{"emoji":"💬","endpoint":"http://localhost:8082/v1/discord/action"}}
---

# Discord Actions for Cinderella

## Overview

Use `discord` to manage Discord operations from Claude Code via Cinderella's local API. The API is compatible with Moltbot's format and runs on `http://localhost:8082/v1/discord/action`.

## Supported Actions

All actions are executed via curl to the local API endpoint:

```bash
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"action":"...","...":"..."}'
```

## Inputs to collect

- For reactions: `channelId`, `messageId`, and an `emoji`.
- For fetchMessage: `guildId`, `channelId`, and `messageId`.
- For sendMessage: `channelId` and `content`.
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
