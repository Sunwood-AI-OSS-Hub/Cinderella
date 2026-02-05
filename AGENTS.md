# AGENTS.md - Cinderella Project

> AIエージェントのためのREADME

## プロジェクト概要

Cinderellaは、Claude Code CLIを複数のインターフェース（Discord Bot、HTTP API）でオーケストレーションするAgenticOS（Agentic Operating System）です。

**技術スタック:**
- Python 3.8+
- FastAPI（HTTP APIサーバー）
- Discord.py 2.3+（Discord Bot）
- Docker Compose（コンテナオーケストレーション）
- Claude Code CLI（AIエージェント基盤）

## コアアーキテクチャ

```
Discordユーザー ⇄ Discord Bot (FastAPI) ⇄ cc-api (HTTP) ⇄ Claude Code CLI
                   ↓
            :8082 (HTTP API)
```

- **`discord-bot/bot.py`**: Discord Bot本体 + FastAPIサーバー
- **`cc-api/server.py`**: Claude Code HTTP API
- **`discord-bot/handlers/`**: Discord操作ハンドラー
- **`discord-bot/debate_handler.py`**: Bot間議論機能

## コーディング規約

### Pythonスタイル
- PEP 8に従う
- 関数シグネチャには型ヒントを使用する
- ドキュメント文字列は英語（内部ロジックのコメントは日本語でも可）
- ログ出力は標準の`logging`モジュールを使用

### Discord Bot規約
- スラッシュコマンドと通常コマンド（`!`プレフィックス）の両方をサポート
- Botの応答はリアクション（⏳→✅/❌）で視覚的にフィードバック
- エラーハンドリングはユーザーフレンドリーに

## エージェント・マネージャー パターン（重要！）

**あなたは何でも屋エージェントではなく、マネージャーです。**

機能を実装する際：
1. **タスクを独立したサブタスクに分解する**
2. **サブエージェントを使用して並列実行する**
3. **結果を調整して統合する**

## プロジェクト構造

```
cinderella/
├── cc-api/                     # Claude Code HTTP API
│   ├── server.py               # FastAPIサーバー
│   └── Dockerfile              # APIサーバーコンテナ
├── discord-bot/                # Discord Botインターフェース
│   ├── bot.py                  # Discord Bot本体 + FastAPI
│   ├── handlers/               # Discord操作ハンドラー
│   ├── debate_handler.py       # Bot間議論機能
│   ├── Dockerfile              # Botコンテナ
│   └── requirements.txt        # Python依存関係
├── browser-api/                # ブラウザ操作API
├── docker-compose.yml          # サービスオーケストレーション
├── .env                        # API Key + DISCORD_TOKEN (Git無視)
├── .env.example                # テンプレート
└── workspace/                  # 作業ディレクトリ
```

## Discord Botコマンド

### 通常コマンド（!プレフィックス）
- `!ask <質問>` - Claudeに質問する
- `!task <タスク>` - スレッドでタスクを処理
- `!debate <トピック>` - Bot間議論を開始
- `!ping` - 動作確認
- `!help` - ヘルプ表示
- `!info` - Bot情報表示

### スラッシュコマンド
- `/ask <質問>` - Claudeに質問する
- `/task <タスク>` - スレッドでタスクを処理
- `/ping` - 動作確認
- `/info` - Bot情報表示
- `/help` - ヘルプ表示

### メンション
- `@BotName <質問>` - メンションだけで質問

## Discord API エンドポイント

### `POST /v1/discord/action`

Claude CodeからDiscordアクションを実行します（Moltbot互換）。

**サポートされているアクション:**
- `react` - メッセージにリアクションを追加
- `sendMessage` - 新しいメッセージを送信
- `sendFile` - ファイルを送信
- `editMessage` - 既存のメッセージを編集
- `deleteMessage` - メッセージを削除
- `readMessages` - メッセージ一覧を取得
- `threadCreate` - スレッドを作成
- `threadReply` - スレッドに返信
- `threadList` - スレッド一覧を取得
- その他多数

## 設定ファイル

- **`.env`**: 環境変数設定（APIキー、Discordトークン等）
- **`docker-compose.yml`**: サービス定義
- **`discord-bot/requirements.txt`**: Python依存関係

## ポート

- **8081**: cc-api HTTPサーバー
- **8082**: discord-bot APIサーバー（Claude Code → Discord 操作用）
- **8083**: browser-api HTTPサーバー

## 一般的なタスク

### 新しいDiscordコマンドを追加
1. `discord-bot/bot.py`でコマンドハンドラーを追加
2. スラッシュコマンドの場合は`@bot.tree.command()`デコレーターを使用
3. 通常コマンドの場合は`@bot.command()`デコレーターを使用
4. ヘルプメッセージを更新

### 新しいDiscordアクションを追加
1. `discord-bot/handlers/`にハンドラー関数を作成
2. `bot.py`の`discord_action()`エンドポイントにアクションを追加
3. `DiscordActionRequest`モデルに必要なフィールドを追加

## テスト戦略

- Discord Botのテストはテストサーバーで行う
- APIエンドポイントのテストはcurlまたはPostmanで実行
- ログを確認してデバッグ

## 心に留めておくこと

- あなたは**マネージャー** - サブエージェントに委任する
- 可能な限りタスクを**並列実行**する
- 結果を**調整・統合**する
- コードを**クリーンでテスト可能**に保つ
- **双方向通信**を意識する（ユーザー→AI、AI→ユーザー）
