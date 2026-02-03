
<div align="center">
  <img src="./assets/header.png" alt="Cinderella Header" width="100%"/>
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3%2B-purple?style=flat-square&logo=discord&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude_Code-CLI-orange?style=flat-square)

# Cinderella - AgenticOS

<a href="README_JA.md"><img src="https://img.shields.io/badge/%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88-%E6%97%A5%E6%9C%AC%E8%AA%9E-white.svg" alt="JA doc"/></a>
<a href="README.md"><img src="https://img.shields.io/badge/Documentation-English-white.svg" alt="EN doc"/></a>

</div>


A local AgenticOS that orchestrates Claude Code CLI with multiple interfaces.

Pre-configured to work with GLM models (Zhipu AI).

**Architecture:**

```
Discord User ⇄ Discord Bot (FastAPI) ⇄ cc-api (HTTP) ⇄ Claude Code CLI
                   ↓
            :8082 (HTTP API)
```

Cinderella supports **bidirectional communication**:
- **User → AI**: Ask questions via Discord or HTTP API
- **AI → User**: Send notifications from Claude Code to Discord via discord-bot API

## Setup

### 1. Get an API Key

Obtain one of the following:

- **Anthropic**: https://console.anthropic.com/ (Official Claude models)
- **Z.AI**: https://open.bigmodel.cn/ (GLM models)

### 2. Configure `.env` File

Copy `.env.example` to `.env` and set the API key you want to use.

**When using Anthropic (Official Claude models):**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx...
```

**When using Z.AI (GLM models):**
```bash
ZAI_API_KEY=your_zai_api_key_here
```

### 3. Switch API in `docker-compose.yml`

In the `environment` section of `docker-compose.yml`, toggle the comments for the API you want to use.

**When using Z.AI (GLM models) (default):**
```yaml
environment:
  # When using Anthropic (Official Claude models)
  # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  # When using Z.AI (GLM models)
  - ANTHROPIC_API_KEY=${ZAI_API_KEY}
```

**When using Anthropic (Official Claude models):**
```yaml
environment:
  # When using Anthropic (Official Claude models)
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  # When using Z.AI (GLM models)
  # - ANTHROPIC_API_KEY=${ZAI_API_KEY}
  # GLM model settings (only effective when using Z.AI)
  # - ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
  # - ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7
  # - ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7
```

### 4. Start Docker Container

```bash
docker compose up -d
```

### 5. Verify Operation

```bash
# Health check
curl http://127.0.0.1:8081/health

# API execution
curl -s http://127.0.0.1:8081/v1/claude/run \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Hello",
    "cwd": "/workspace",
    "allowed_tools": ["Read"],
    "timeout_sec": 30
  }'
```

### 6. (Optional) Discord Bot Setup

If you want to use Claude via Discord:

1. **Create a Discord Bot**
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token

2. **Add Environment Variables to `.env`**

Add the following lines to your `.env` file:

```bash
# Required: Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# Optional: API Key for endpoint authentication
# If set, requests to /v1/discord/action must include this key in the x-api-key header
# If not set, the endpoint is accessible without authentication
DISCORD_BOT_API_KEY=your_discord_bot_api_key_here
```

3. **Start Services**

```bash
docker compose up -d
```

4. **Use in Discord**

You can interact with the bot in two ways:

**Mention the bot directly (recommended):**
```
@BotName Show me the current date and time
@BotName ping
```

**Or use commands:**
```
!ask Show me the current date and time
!ping
!help
!info
```

**Reaction Indicators:**
- ⏳ Processing your request...
- ✅ Request completed successfully
- ❌ Request failed (check logs for details)

## API Endpoints

### `GET /health`

Checks the server status.

```json
{"ok": true}
```

### `POST /v1/claude/run`

Executes Claude Code.

**Request:**

```json
{
  "prompt": "Summarize the README of this repository",
  "cwd": "/workspace",
  "allowed_tools": ["Read", "Bash", "Edit"],
  "timeout_sec": 300
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | ✅ | Prompt to pass to Claude |
| `cwd` | string | ❌ | Execution directory (default: null) |
| `allowed_tools` | array | ❌ | Allowed tools (default: ["Read"]) |
| `timeout_sec` | int | ❌ | Timeout in seconds (default: 300) |

**Response:**

```json
{
  "exit_code": 0,
  "stdout_json": {
    "type": "result",
    "subtype": "success",
    "result": "..."
  }
}
```

### `POST /v1/discord/action`

Execute Discord actions (Moltbot-compatible) from Claude Code.

**Authentication (Optional):**

If `DISCORD_BOT_API_KEY` is set in your environment variables, requests must include the API key in the `x-api-key` header:

```bash
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_discord_bot_api_key_here" \
  -d '{"action":"react","channelId":"123","messageId":"456","emoji":"✅"}'
```

If `DISCORD_BOT_API_KEY` is not set, the endpoint is accessible without authentication.

**Supported Actions:**

- `react` - Add reaction to a message
- `sendMessage` - Send a new message
- `editMessage` - Edit an existing message
- `deleteMessage` - Delete a message

**Request Examples:**

```json
// React to a message
{
  "action": "react",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "emoji": "✅"
}

// Send a message
{
  "action": "sendMessage",
  "channelId": "1234567890",
  "content": "Hello from Claude Code!"
}

// Edit a message
{
  "action": "editMessage",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "content": "Updated message"
}

// Delete a message
{
  "action": "deleteMessage",
  "channelId": "1234567890",
  "messageId": "0987654321"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "message": "Reaction added"
  }
}
```

**Usage from Claude Code:**

Claude Code can execute Discord actions using curl:

```bash
# React to a message (with API key authentication)
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_discord_bot_api_key_here" \
  -d '{"action":"react","channelId":"123","messageId":"456","emoji":"✅"}'

# Send a message (with API key authentication)
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_discord_bot_api_key_here" \
  -d '{"action":"sendMessage","channelId":"123","content":"Hello from Claude Code!"}'

# Without authentication (if DISCORD_BOT_API_KEY is not set)
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"action":"react","channelId":"123","messageId":"456","emoji":"✅"}'
```

## GLM Model Configuration

When using Z.AI (GLM models), you can configure the following settings in `.env` or environment variables:

```bash
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7
```

Alternatively, these are pre-configured in docker-compose.yml.

## Mugen Environment (MultimediaOS-MUGEN)

A Docker environment configuration optimized for the MultimediaOS-MUGEN project is also available.

### Mugen Environment Features

- **Project Directory**: Mounts `config/agent2/MultimediaOS-MUGEN` as the workspace
- **Media Directory**: Accessible from Claude Code for media file operations
- **Git Configuration**: Supports per-agent Git user configuration
- **GitHub Integration**: Supports per-agent GitHub PAT (Personal Access Token)

### Mugen Environment Setup

1. **Add Git and GitHub settings to `.env` file**

```bash
# GitHub Personal Access Token for AYANO
GH_PAT_AYANO=your_github_pat_here

# Git user settings for AYANO
GIT_USER_NAME_AYANO=AYANO
GIT_USER_EMAIL_AYANO=ayano@example.com
```

2. **Configure additional API keys in `.env` file**

```bash
# FAL API Key (for fal-ai skills)
FAL_KEY=your_fal_key_here

# Google API Key (for agentic-vision-gemini skills)
GOOGLE_API_KEY=your_google_api_key_here
```

3. **Start the Mugen environment docker-compose**

```bash
docker compose -f docker-compose-mugen.yml up -d
```

### Per-Agent Configuration

In the Mugen environment, multiple agents can each have their own Git/GitHub settings:

| Agent | Git Username | Git Email | GitHub PAT |
|-------|--------------|-----------|------------|
| AYANO | `GIT_USER_NAME_AYANO` | `GIT_USER_EMAIL_AYANO` | `GH_PAT_AYANO` |
| SEIRA | `GIT_USER_NAME_SEIRA` | `GIT_USER_EMAIL_SEIRA` | `GH_PAT_SEIRA` |
| MIREL | `GIT_USER_NAME_MIREL` | `GIT_USER_EMAIL_MIREL` | `GH_PAT_MIREL` |

### Port Configuration

In the Mugen environment, you can customize the port for each service in the `.env` file:

```bash
# CC API Port (default: 8081)
CC_API_PORT=8081

# Browser API Port (default: 8083)
BROWSER_API_PORT=8083

# Browser VNC Port (default: 5900)
BROWSER_VNC_PORT=5900

# Browser noVNC Port (default: 7900)
BROWSER_NOVNC_PORT=7900

# Discord Bot Port (default: 8082)
DISCORD_BOT_PORT=8082
```

### File Structure (Mugen Environment)

```
cinderella/
├── docker-compose-mugen.yml     # Docker compose configuration for Mugen environment
├── config/agent2/MultimediaOS-MUGEN/  # Workspace (project directory)
├── cc-api/
│   ├── entrypoint.sh            # Entrypoint script for Git configuration
│   └── Dockerfile               # Includes Git and entrypoint support
└── .SourceSageignore            # SourceSage ignore settings (excludes config/ directory)
```

## Logging

Both `cc-api` and `discord-bot` support detailed logging for debugging and monitoring.

**Environment Variables:**

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=DEBUG

# For cc-api: Control CORS allowed origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Log Features:**
- **cc-api**: Logs API requests, responses, and errors. Sensitive prompt content is automatically redacted as `[REDACTED]` for security.
- **discord-bot**: Logs bot events, command executions, and errors with detailed context.

**View Logs:**

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f cc-api
docker compose logs -f discord-bot

# View logs with tail
docker compose logs --tail=100 -f
```

## Ports

- **8081**: cc-api HTTP server
- **8082**: discord-bot API server (for Claude Code → Discord actions)

## File Structure

```
cinderella/
├── cc-api/                     # Claude Code HTTP API
│   ├── server.py               # FastAPI server
│   └── Dockerfile              # API server container
├── discord-bot/                # Discord Bot interface
│   ├── bot.py                  # Discord Bot本体 + FastAPI
│   ├── Dockerfile              # Bot container
│   └── requirements.txt        # Python dependencies
├── docker-compose.yml          # Service orchestration
├── .env                        # API Key + DISCORD_TOKEN (Git ignored)
├── .env.example                # Template
└── workspace/                  # Work directory
```

## References

- [Claude Code Official Documentation](https://code.claude.com/docs/overview)
- [Z.AI GLM Model Configuration](https://docs.z.ai/devpack/tool/claude)
