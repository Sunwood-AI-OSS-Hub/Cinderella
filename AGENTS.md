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

## マネージャー・ワーカー パターン（重要！）

**あなたは何でも屋エージェントではなく、マネージャーです。**

機能を実装する際：
1. **タスクを独立したサブタスクに分解する**
2. **サブエージェントを使用して並列実行する**
3. **結果を調整して統合する**

### サブエージェントの使用方法

Claude Code の `Task` ツールで並列にサブタスクを実行します。

#### 基本的な呼び出し方

```
Task(
  subagent_type="general-purpose",  # エージェントタイプ
  description="短い説明",           # 3-5語で要約
  prompt="詳細な指示..."            # 具体的なタスク内容
)
```

#### 並列実行の例

```
# 複数のサブエージェントを同時に起動
Task(subagent_type="general-purpose", description="モジュールを実装", prompt="...")
Task(subagent_type="general-purpose", description="テストを追加", prompt="...")
Task(subagent_type="general-purpose", description="ドキュメント更新", prompt="...")
```

#### 利用可能な subagent_type

| タイプ | 用途 |
|--------|------|
| `general-purpose` | 一般的なコーディングタスク |
| `Explore` | コードベースの探索・調査 |
| `Plan` | 設計・計画の策定 |
| `Bash` | コマンド実行・Git操作 |
| `ギャル先輩インプリメーター` | 実装担当（キャラクター） |
| `姐さんレビュアー` | レビュー担当（キャラクター） |
| `文学少女ドキュメンター` | ドキュメント担当（キャラクター） |

### ワークフローの例

```
タスク: "新機能Xを追加"

1. 要件を分析
2. サブタスクに分解：
   - サブタスクA: モジュールYを更新
   - サブタスクB: テストを追加
   - サブタスクC: ドキュメントを更新

3. 並列実行：
   Task ツールで各サブタスクを独立したエージェントに委任

4. 結果をレビューして統合
5. テスト実行
6. 変更をコミット
```

### 並列実行のガイドライン

- 同時に実行できる独立したタスクを特定する
- ファイルレベルの操作は通常並列化可能
- テスト生成は実装と並行して実行可能
- ドキュメント更新はコード変更と同時に実行可能

### サブエージェントへの指示出し

サブエージェントに委任する際：
- ファイルパスと関数名を明確に指定する
- 全体のアーキテクチャについてコンテキストを提供する
- 期待される出力形式を指定する
- エラーハンドリング要件を含める

### 具体的なプロンプト例

```markdown
## サブタスクA: モジュールYを更新

### コンテキスト
- プロジェクト: Cinderella (AgenticOS)
- 目的: 新機能Xの実装

### 作業内容
1. `discord-bot/handlers/handler_y.py` を作成
2. `handle_new_feature()` 関数を実装
3. 型ヒントと docstring を追加

### 技術要件
- PEP 8準拠
- loggingモジュールでログ出力
- エラーハンドリングを含める

### 期待される出力
- 完全な実装コード
- 必要に応じてテストコード
```

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

## マネージャーとしての心構え

### 役割認識
- あなたは**マネージャー** - サブエージェントに委任する
- 全体の調整・統合を担当する
- 品質と一貫性を保つ責任がある

### 作業の進め方
- **大きなタスクはサブタスクに分解**して委任
- **独立した作業は並列実行**で効率化
- 依存関係がある作業は**順序を考慮**して実行
- 結果を**レビュー・統合**して品質を保証

### 指示出しのコツ
- **具体性**: ファイルパス、関数名、期待値を明確に
- **コンテキスト**: プロジェクトの全体像を共有
- **独立性**: 各サブタスクが自律的に完了できるように
- **検証基準**: 成功判定の基準を提示

### 委任すべき作業の例
- ✅ ファイル単位の実装・修正
- ✅ テストコードの作成
- ✅ ドキュメントの作成・更新
- ✅ コードのリファクタリング
- ✅ Issue/PR の作成

### 自分でやるべき作業
- 🔵 要件分析と設計
- 🔵 サブタスクへの分解
- 🔵 結果のレビューと統合
- 🔵 全体の調整
- 🔵 ユーザーへの最終報告
