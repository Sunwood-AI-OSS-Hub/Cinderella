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

Claude Code CLI を複数のインターフェースでオーケストレーションするローカルAgenticOS。

<a href="README_JA.md"><img src="https://img.shields.io/badge/%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88-%E6%97%A5%E6%9C%AC%E8%AA%9E-white.svg" alt="JA doc"/></a>
<a href="README.md"><img src="https://img.shields.io/badge/Documentation-English-white.svg" alt="EN doc"/></a>

</div>


GLMモデル（智谱AI/Z.AI）で動作するように設定済みです。

**アーキテクチャ:**

```
Discordユーザー ⇄ Discord Bot (FastAPI) ⇄ cc-api (HTTP) ⇄ Claude Code CLI
                   ↓
            :8082 (HTTP API)
```

Cinderellaは**双方向通信**をサポートしています：
- **ユーザー → AI**: DiscordまたはHTTP API経由で質問
- **AI → ユーザー**: Claude CodeからDiscordへ通知送信（discord-bot API経由）

## セットアップ

### 1. APIキーを取得

いずれか一方を取得してください：

- **Anthropic**: https://console.anthropic.com/ （公式Claudeモデル）
- **Z.AI**: https://open.bigmodel.cn/ （GLMモデル）

### 2. `.env` ファイルを設定

`.env.example` をコピーして `.env` を作成し、使用するAPIキーを設定してください。

**Anthropic（公式Claudeモデル）を使用する場合:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx...
```

**Z.AI（GLMモデル）を使用する場合:**
```bash
ZAI_API_KEY=your_zai_api_key_here
```

### 3. `docker-compose.yml` でAPIを切り替え

`docker-compose.yml` の `environment` セクションで、使用するAPIのコメントアウトを切り替えてください。

**Z.AI (GLMモデル) を使用する場合（デフォルト）:**
```yaml
environment:
  # Anthropic（公式Claudeモデル）を使用する場合
  # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  # Z.AI（GLMモデル）を使用する場合
  - ANTHROPIC_API_KEY=${ZAI_API_KEY}
```

**Anthropic（公式Claudeモデル）を使用する場合:**
```yaml
environment:
  # Anthropic（公式Claudeモデル）を使用する場合
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  # Z.AI（GLMモデル）を使用する場合
  # - ANTHROPIC_API_KEY=${ZAI_API_KEY}
  # GLMモデル設定（Z.AIを使用する場合のみ有効）
  # - ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
  # - ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7
  # - ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7
```

### 4. Dockerコンテナを起動

```bash
docker compose up -d
```

### 5. 動作確認

```bash
# ヘルスチェック
curl http://127.0.0.1:8081/health

# API実行
curl -s http://127.0.0.1:8081/v1/claude/run \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "こんにちは",
    "cwd": "/workspace",
    "allowed_tools": ["Read"],
    "timeout_sec": 30
  }'
```

### 6. （任意）Discord Botのセットアップ

Discord経由でClaudeを使用したい場合：

1. **Discord Botを作成**
   - https://discord.com/developers/applications にアクセス
   - 新しいアプリケーションを作成
   - 「Bot」セクションでボットを作成
   - ボットトークンをコピー

2. **`.env` に DISCORD_TOKEN を追加**

`.env` ファイルに以下を追加してください：

```bash
DISCORD_TOKEN=your_discord_bot_token_here
```

3. **サービスを起動**

```bash
docker compose up -d
```

4. **Discordで使用**

ボットとの対話は2つの方法で可能です：

**ボットをメンションする（推奨）：**
```
@BotName 現在の日時を表示して
@BotName ping
```

**またはコマンドを使用：**
```
!ask 現在の日時を表示して
!ping
!help
!info
```

**リアクションインジケーター：**
- ⏳ リクエストを処理中...
- ✅ リクエストが正常に完了
- ❌ リクエストが失敗（ログで詳細を確認）

## APIエンドポイント

### `GET /health`

サーバーの状態を確認します。

```json
{"ok": true}
```

### `POST /v1/claude/run`

Claude Codeを実行します。

**リクエスト:**

```json
{
  "prompt": "このリポジトリのREADMEを要約して",
  "cwd": "/workspace",
  "allowed_tools": ["Read", "Bash", "Edit"],
  "timeout_sec": 300
}
```

**パラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| `prompt` | string | ✅ | Claudeに渡すプロンプト |
| `cwd` | string | ❌ | 実行ディレクトリ（デフォルト: null） |
| `allowed_tools` | array | ❌ | 許可するツール（デフォルト: ["Read"]） |
| `timeout_sec` | int | ❌ | タイムアウト秒数（デフォルト: 300） |

**レスポンス:**

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

Claude CodeからDiscordアクションを実行します（Moltbot互換）。

**サポートされているアクション:**

- `react` - メッセージにリアクションを追加
- `sendMessage` - 新しいメッセージを送信
- `editMessage` - 既存のメッセージを編集
- `deleteMessage` - メッセージを削除

**リクエスト例:**

```json
// メッセージにリアクション
{
  "action": "react",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "emoji": "✅"
}

// メッセージを送信
{
  "action": "sendMessage",
  "channelId": "1234567890",
  "content": "こんにちは、Claude Codeから！"
}

// メッセージを編集
{
  "action": "editMessage",
  "channelId": "1234567890",
  "messageId": "0987654321",
  "content": "編集したメッセージ"
}

// メッセージを削除
{
  "action": "deleteMessage",
  "channelId": "1234567890",
  "messageId": "0987654321"
}
```

**レスポンス:**

```json
{
  "success": true,
  "data": {
    "message": "Reaction added"
  }
}
```

**Claude Codeからの使用方法:**

Claude Codeはcurlを使ってDiscordアクションを実行できます：

```bash
# メッセージにリアクション
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"action":"react","channelId":"123","messageId":"456","emoji":"✅"}'

# メッセージを送信
curl -s http://localhost:8082/v1/discord/action \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"action":"sendMessage","channelId":"123","content":"こんにちは、Claude Codeから！"}'
```

## GLMモデル設定

Z.AI（GLMモデル）を使用する場合、`.env` または環境変数で以下の設定が可能です：

```bash
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7
```

または、docker-compose.ymlで事前に設定されています。

## ロギング

`cc-api` と `discord-bot` の両方が、デバッグと監視のための詳細なロギングをサポートしています。

**環境変数:**

```bash
# ログレベルを設定 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=DEBUG

# cc-api用: CORS許可オリジンを制御
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**ログ機能:**
- **cc-api**: APIリクエスト、レスポンス、エラーをログ記録。セキュリティのため、機密性の高いプロンプト内容は自動的に `[REDACTED]` に置き換えられます。
- **discord-bot**: ボットイベント、コマンド実行、エラーを詳細なコンテキストと共にログ記録。

**ログの確認:**

```bash
# すべてのログを表示
docker compose logs -f

# 特定のサービスのログを表示
docker compose logs -f cc-api
docker compose logs -f discord-bot

# 最新のログを表示
docker compose logs --tail=100 -f
```

## ポート

- **8081**: cc-api HTTPサーバー
- **8082**: discord-bot APIサーバー（Claude Code → Discord 操作用）

## ファイル構造

```
cinderella/
├── cc-api/                     # Claude Code HTTP API
│   ├── server.py               # FastAPIサーバー
│   └── Dockerfile              # APIサーバーコンテナ
├── discord-bot/                # Discord Botインターフェース
│   ├── bot.py                  # Discord Bot本体 + FastAPI
│   ├── Dockerfile              # Botコンテナ
│   └── requirements.txt        # Python依存関係
├── docker-compose.yml          # サービスオーケストレーション
├── .env                        # API Key + DISCORD_TOKEN (Git無視)
├── .env.example                # テンプレート
└── workspace/                  # 作業ディレクトリ
```

## 参考資料

- [Claude Code 公式ドキュメント](https://code.claude.com/docs/overview)
- [Z.AI GLMモデル設定](https://docs.z.ai/devpack/tool/claude)
