# AGENTS.md - SourceSage プロジェクト

> AIコーディングエージェントのためのREADME

## プロジェクト概要

SourceSageは、リポジトリを分析してAIに優しいドキュメントを生成するツールです。Repository Summary生成とRelease Report生成の2つの主要機能を提供します。

**技術スタック:**
- Python 3.8+
- パッケージマネージャー: uv / pip
- ビルドシステム: hatchling
- CLI: argparse + Rich（美しいターミナル出力）

## コアアーキテクチャ

- **`sourcesage/cli.py`**: メインCLIエントリーポイント
- **`sourcesage/core.py`**: コア分析エンジン
- **`sourcesage/modules/DocuSum/`**: リポジトリサマリー生成
- **`sourcesage/modules/DiffReport/`**: Git差分とリリースレポート生成

## コーディング規約

### Pythonスタイル
- PEP 8に従う
- 関数シグネチャには型ヒントを使用する
- ドキュメント文字列は英語（内部ロジックのコメントは日本語でも可）
- ログ出力は`loguru`をRichスタイルで使用

### CLI規約
- 引数解析には`argparse`を使用
- 出力には`rich.console.Console`を使用
- `--language`フラグで国際化（en/ja）をサポート
- `art`ライブラリで起動時にASCIIアートバナーを表示

## マネージャー・ワーカー パターン（重要！）

**あなたは何でも屋エージェントではなく、マネージャーです。**

機能を実装する際：
1. **タスクを独立したサブタスクに分解する**
2. **`ccd-glm`サブエージェントを使用して並列実行する**
3. **結果を調整して統合する**

### ccd-glm サブエージェントの使用方法

並列でサブタスクを実行するには：
```bash
ccd-glm -p "具体的な指示"
```

### ワークフローの例

```
タスク: "新機能Xを追加"

1. 要件を分析
2. サブタスクに分解：
   - サブタスクA: モジュールYを更新
   - サブタスクB: テストを追加
   - サブタスクC: ドキュメントを更新

3. 並列実行：
   ccd-glm -p "サブタスクAの指示..." &
   ccd-glm -p "サブタスクBの指示..." &
   ccd-glm -p "サブタスクCの指示..." &
   wait

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

`ccd-glm`に委任する際：
- ファイルパスと関数名を明確に指定する
- 全体のアーキテクチャについてコンテキストを提供する
- 期待される出力形式を指定する
- エラーハンドリング要件を含める

## プロジェクト構造

```
sourcesage/
├── __init__.py
├── cli.py              # CLIエントリーポイント (argparse, Rich)
├── core.py             # メイン分析エンジン
├── logging_utils.py    # Richログ設定
└── modules/
    ├── DocuSum/        # リポジトリサマリー
    │   ├── __init__.py
    │   └── ...
    └── DiffReport/     # Git差分レポート
        ├── __init__.py
        ├── git_diff.py
        └── markdown_report.py
```

## 設定ファイル

- **`.SourceSageignore`**: 無視パターン（パッケージデフォルトから自動生成）
- **`.gitignore`**: ファイルを無視するためにも使用（v7.2.0以降デフォルト）
- **`sourcesage/config/language_map.json`**: 拡張子と言語のマッピング

## 出力先

- Repository Summary: `.SourceSageAssets/Repository_summary.md`
- Release Report: `.SourceSageAssets/RELEASE_REPORT/Report_{latest_tag}.md`

## 開発ワークフロー

```bash
# ローカルで実行
uv run sage

# オプション付きで実行
uv run sage -o ./output --repo ./myproject

# テスト実行
uv run pytest

# コードフォーマット
uv run black sourcesage/
uv run isort sourcesage/
```

## 重要な設計判断

1. **国際化**: ユーザー向けメッセージはすべて`--language`でen/jaをサポート
2. **適切なデフォルト**: `.SourceSageignore`がなければ自動生成
3. **リッチな出力**: 美しいターミナルUIのためにRichライブラリを使用
4. **非推奨機能**: `--diff`フラグは非推奨（LLMのコマンド実行能力が向上）

## 一般的なタスク

### 新しいCLIオプションを追加
1. `cli.py:add_arguments()`で引数を追加
2. ドキュメント用に`render_rich_help()`を更新
3. `SourceSage`コアクラスに渡す

### 新しいモジュールを追加
1. `sourcesage/modules/`配下に作成
2. `__init__.py`を追加
3. `core.py`または`cli.py`でインポートして使用

### 言語サポートを更新
1. `cli.py`の辞書にメッセージを追加
2. `msg.get(key, default)`パターンを使用
3. `-l en`と`-l ja`でテスト

## テスト戦略

- 単体テストには`pytest`を使用
- 英語と日本語の出力両方をテスト
- CI/CDではGit操作をモック

## リリースプロセス

1. `pyproject.toml`でバージョンを更新
2. `RELEASE_NOTES.md`を更新
3. Gitタグを作成
4. GitHub ActionsでPyPIに公開

## 心に留めておくこと

- あなたは**マネージャー** - `ccd-glm`ワーカーに委任する
- 可能な限りタスクを**並列実行**する
- 結果を**調整・統合**する
- コードを**クリーンでテスト可能**に保つ
