<img src="https://raw.githubusercontent.com/Sunwood-AI-OSS-Hub/Cinderella/refs/heads/main/assets/release-header-v0.2.0b.png" alt="v0.2.0 Release"/>

# v0.2.0 - Agentic Vision / エージェント的ビジョン

**リリース日 / Release Date:** 2026-01-30

---

## 日本語 / Japanese

### 概要

Cinderella v0.2.0 は、**Agentic Vision** の力で画像理解と対話型AI体験を次のレベルへと進化させました。

Gemini 3 Flash の最先端視覚機能を活用し、Think-Act-Observe ループによる自律的画像分析、ズームイン検査、アノテーション、データ可視化を実現。Discord Bot はファイル添付、議論機能、メッセージ返信を備えた真の対話型エージェントへと進化しました。

本リリースには **9つのプルリクエスト** (#7, #9, #11, #13, #15, #16, #18, #20, #22) がマージされ、v0.1.0 以降の全ての改善が含まれています。

### 新機能 / What's New

#### 🔮 Agentic Vision (エージェント的ビジョン) - #20, #22

- **Gemini 3 Flash Preview 対応**: 最新の Gemini 3 Flash モデルに対応 (#22)
- **Think-Act-Observe ループ**: 自律的な画像理解とタスク実行 (#20)
- **ズームイン検査**: 高解像度画像の詳細分析 (#20)
- **アノテーション機能**: 画像へのバウンディングボックスとラベル描画 (#20)
- **データ可視化**: 表やグラフからのデータ抽出・プロット生成 (#20)
- **バッチ分析**: 複数画像の一括処理 (#22)
- **コード実行による画像操作**: Python実行環境での動的画像処理 (#22)
- **リファクタリング**: image_utils, batch_analyze, agentic_vision モジュールの改善 (#22)

#### 🤖 Discord Bot 機能拡張 - #7, #9, #11, #13, #16, #18, #22

- **マルチサービス構成への移行**: Docker Compose で cc-api と discord-bot を分離 (#7)
- **メンション対応**: `@Cinderella` で呼び出し可能 (#9)
- **ロギング機能**: 詳細な実行ログとデバッグ情報 (#11)
- **FastAPI サーバー**: Moltbot 互換 API エンドポイントの実装 (#13)
- **ファイル添付対応**: 画像ファイルを添付して分析可能 (#22)
- **議論機能**: `!debate` コマンドで複数視点の議論を生成 (#18)
- **メッセージ返信**: スレッドへの返信と対話履歴の管理 (#18)
- **リアクション機能**: メッセージへのリアクション追加 (#11)
- **ハンドラーのモジュール化**: Discordアクションハンドラーの独立 (#15, #16)

#### 🌐 Browser API サービス - #20

- **新しいサービス追加**: browser-api サービスを docker-compose に追加
- **CORS 設定**: セキュアなクロスオリジンアクセス
- **例外処理の強化**: エラーハンドリングの改善

#### 🛠️ Claude Code Skills - #16, #20

- **Discord スキル**: `/agentic-vision-gemini` スキルで高度な画像分析をコマンド一つで実行可能
- **スキル構成**: CLAUDE.md を含むプロジェクト設定の追加 (#22)

### バグ修正 / Bug Fixes

- **セキュリティ強化**: CORS設定と環境変数検証の改善 (#11, #20)
- **コード品質**: 玲子姐さんと美咲先輩によるレビュー反映 (#7, #22)
- **Dockerfile 改善**: cc-api に curl、google-genai を追加 (#20, #22)
- **ハンドラー修正**: スレッド取得を `fetch_channel` に変更 (#16)
- **エンドポイントURL修正**: Discord スキルの URL を修正 (#20)

### インフラ変更 / Infrastructure Changes

- **Google API キー**: `.env.example` に `GOOGLE_API_KEY` を追加 (#22)
- **Docker ボリューム**: ワークスペースとメディアディレクトリの設定を更新 (#7, #20)
- **Gitignore**: browser-api 関連、plans、tmp フォルダを追加 (#16, #20)
- **テスト構成**: テストスイートを追加・再構成 (#16)
- **cinderella ユーザー**: セキュリティのための専用ユーザーとsudo権限を設定 (#9)

### ドキュメント / Documentation

- **Agentic Vision README**: APIリファレンスとユースケースを更新 (#22)
- **Browser API README**: セットアップ手順を追加 (#20)
- **Discord Bot ドキュメント**: 返信機能と議論機能のドキュメント追加 (#18)
- **テスト README**: パスを最新化 (#16)
- **日本語README**: 言語切り替えバッジを追加 (#7)

### テスト / Tests

- **Discord Bot テストスイート**: メッセージ返信、ファイル添付のテスト追加 (#22)
- **ハンドラー個別テスト**: 各ハンドラーの単体テストと統合テスト (#15)
- **API テスト**: discord-bot API のフル機能テストスクリプト (#13)

---

## English

### Overview

Cinderella v0.2.0 evolves image understanding and conversational AI experiences to the next level with the power of **Agentic Vision**.

Leveraging Gemini 3 Flash's cutting-edge vision capabilities, we now support autonomous image analysis via Think-Act-Observe loops, zoom-in inspection, annotation, and data visualization. The Discord Bot has evolved into a true conversational agent with file attachments, debate functionality, and message replies.

This release includes **9 pull requests** (#7, #9, #11, #13, #15, #16, #18, #20, #22), incorporating all improvements since v0.1.0.

### What's New

#### 🔮 Agentic Vision - #20, #22

- **Gemini 3 Flash Preview Support**: Compatible with the latest Gemini 3 Flash model (#22)
- **Think-Act-Observe Loop**: Autonomous image understanding and task execution (#20)
- **Zoom-in Inspection**: Detailed analysis of high-resolution images (#20)
- **Annotation Features**: Bounding boxes and label rendering on images (#20)
- **Data Visualization**: Data extraction and plot generation from charts and graphs (#20)
- **Batch Analysis**: Process multiple images at once (#22)
- **Code Execution for Image Manipulation**: Dynamic image processing via Python execution environment (#22)
- **Refactoring**: image_utils, batch_analyze, agentic_vision module improvements (#22)

#### 🤖 Discord Bot Enhancements - #7, #9, #11, #13, #16, #18, #22

- **Multi-Service Architecture**: Separated cc-api and discord-bot in Docker Compose (#7)
- **Mention Support**: Invoke with `@Cinderella` (#9)
- **Logging Features**: Detailed execution logs and debug information (#11)
- **FastAPI Server**: Moltbot-compatible API endpoint implementation (#13)
- **File Attachment Support**: Analyze images by attaching them directly (#22)
- **Debate Feature**: Generate multi-perspective discussions with `!debate` command (#18)
- **Message Replies**: Reply to threads and manage conversation history (#18)
- **Reaction Features**: Add reactions to messages (#11)
- **Handler Modularization**: Independent Discord action handlers (#15, #16)

#### 🌐 Browser API Service - #20

- **New Service**: Added browser-api service to docker-compose
- **CORS Configuration**: Secure cross-origin access
- **Enhanced Exception Handling**: Improved error handling

#### 🛠️ Claude Code Skills - #16, #20

- **Discord Skills**: Execute advanced image analysis with `/agentic-vision-gemini` command
- **Skill Configuration**: Project configuration including CLAUDE.md (#22)

### Bug Fixes

- **Security Enhancements**: Improved CORS settings and environment variable validation (#11, #20)
- **Code Quality**: Reflected reviews from Reiko and Misaki (#7, #22)
- **Dockerfile Improvements**: Added curl and google-genai to cc-api (#20, #22)
- **Handler Fixes**: Changed thread fetching to `fetch_channel` (#16)
- **Endpoint URL Fixes**: Corrected Discord skill URLs (#20)

### Infrastructure Changes

- **Google API Key**: Added `GOOGLE_API_KEY` to `.env.example` (#22)
- **Docker Volumes**: Updated workspace and media directory configurations (#7, #20)
- **Gitignore**: Added browser-api related, plans, and tmp folders (#16, #20)
- **Test Configuration**: Added and reorganized test suites (#16)
- **cinderella User**: Dedicated user and sudo permissions for security (#9)

### Documentation

- **Agentic Vision README**: Updated API reference and use cases (#22)
- **Browser API README**: Added setup instructions (#20)
- **Discord Bot Documentation**: Added docs for reply and debate features (#18)
- **Test README**: Updated paths (#16)
- **Japanese README**: Added language toggle badges (#7)

### Tests

- **Discord Bot Test Suite**: Added tests for message replies and file attachments (#22)
- **Handler Unit Tests**: Individual and integration tests for each handler (#15)
- **API Tests**: Full-featured test scripts for discord-bot API (#13)

---

## Pull Requests / プルリクエスト

このリリースには以下のプルリクエストが含まれています：

This release includes the following pull requests:

- #7 - Modular structure and Docker Compose multi-service setup
- #9 - cc-api security improvements and mention support
- #11 - API logging and mention enhancements
- #13 - Discord Bot FastAPI server with Moltbot-compatible API
- #15 - Discord action handler modularization
- #16 - Test configuration refactoring and Discord Skills
- #18 - Debate feature and message reply functionality
- #20 - Browser API service and Agentic Vision
- #22 - Agentic Vision update with Gemini 3 Flash preview support

---

## Quick Start / クイックスタート

```bash
# 1. Google API Key を設定 / Set Google API Key
cp .env.example .env
# Edit .env: GOOGLE_API_KEY=your_key_here

# 2. Docker で起動 / Start with Docker
docker compose up -d

# 3. Agentic Vision を実行 / Run Agentic Vision
curl -X POST http://127.0.0.1:8081/v1/agentic-vision/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg", "prompt": "Describe this image in detail"}'
```

### Discord Bot Usage / Discord Bot の使用

```
# 画像を添付してメンション / Attach image and mention
@Cinderella この画像を分析して

# 議論を開始 / Start debate
!debate テーマ: AIの倫理について
```

---

## Magic Footnote

> "Vision is the art of seeing what is invisible to others"
>
> — Jonathan Swift

このリリースは、単なる画像分析ツールから真の視覚的エージェントへの進化を表しています。Agentic Vision は、画像を「見る」だけでなく「理解」し、「考え」「行動」する新しい時代の幕開けです。

This release represents the evolution from a simple image analysis tool to a true visual agent. Agentic Vision marks the dawn of a new era where AI doesn't just "see" images, but "understands", "thinks", and "acts" upon them.
