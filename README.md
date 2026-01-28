
<div align="center">
  <img src="./assets/header.png" alt="Cinderella Header" width="600"/>
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3%2B-purple?style=flat-square&logo=discord&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude_Code-CLI-orange?style=flat-square)

# Cinderella - AgenticOS

<a href="README.md"><img src="https://img.shields.io/badge/Documentation-English-white.svg" alt="EN doc"/></a>

</div>


A local AgenticOS that orchestrates Claude Code CLI with multiple interfaces.

Pre-configured to work with GLM models (Zhipu AI).

**Architecture:**

```
Discord User → Discord Bot → cc-api (HTTP) → Claude Code CLI
```

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

2. **Add DISCORD_TOKEN to `.env`**

Add the following line to your `.env` file:

```bash
DISCORD_TOKEN=your_discord_bot_token_here
```

3. **Start Services**

```bash
docker compose up -d
```

4. **Use in Discord**

```
!ask 現在の日時を表示して
!ping
```

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

## GLM Model Configuration

When using Z.AI (GLM models), you can configure the following settings in `.env` or environment variables:

```bash
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7
```

Alternatively, these are pre-configured in docker-compose.yml.

## Ports

- **8081**: HTTP server

## File Structure

```
cinderella/
├── cc-api/                     # Claude Code HTTP API
│   ├── server.py               # FastAPI server
│   └── Dockerfile              # API server container
├── discord-bot/                # Discord Bot interface
│   ├── bot.py                  # Discord Bot本体
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
