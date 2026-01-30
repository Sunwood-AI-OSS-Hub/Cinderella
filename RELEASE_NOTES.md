<img src="https://raw.githubusercontent.com/Sunwood-AI-OSS-Hub/Cinderella/refs/heads/main/assets/release-header-v0.2.0.svg" alt="v0.2.0 Release"/>

# v0.2.0 - Agentic Vision / エージェント的ビジョン

**リリース日 / Release Date:** 2026-01-30

---

## 日本語 / Japanese

### 概要

Cinderella v0.2.0 は、**Agentic Vision** の力で画像理解と対話型AI体験を次のレベルへと進化させました。

Gemini 3 Flash の最先端視覚機能を活用し、Think-Act-Observe ループによる自律的画像分析、ズームイン検査、アノテーション、データ可視化を実現。Discord Bot はファイル添付、議論機能、メッセージ返信を備えた真の対話型エージェントへと進化しました。

### 新機能 / What's New

#### 🔮 Agentic Vision (エージェント的ビジョン)

- **Gemini 3 Flash Preview 対応**: 最新の Gemini 3 Flash モデルに対応
- **Think-Act-Observe ループ**: 自律的な画像理解とタスク実行
- **ズームイン検査**: 高解像度画像の詳細分析
- **アノテーション機能**: 画像へのバウンディングボックスとラベル描画
- **データ可視化**: 表やグラフからのデータ抽出・プロット生成
- **バッチ分析**: 複数画像の一括処理
- **コード実行による画像操作**: Python実行環境での動的画像処理

#### 🤖 Discord Bot 機能拡張

- **ファイル添付対応**: 画像ファイルを添付して分析可能
- **議論機能**: `!debate` コマンドで複数視点の議論を生成
- **メッセージ返信**: スレッドへの返信と対話履歴の管理
- **メンション対応**: `@Cinderella` で呼び出し可能
- **リアクション機能**: メッセージへのリアクション追加
- **ログ改善**: 詳細な実行ログとデバッグ情報

#### 🌐 Browser API サービス

- **新しいサービス追加**: browser-api サービスを docker-compose に追加
- **CORS 設定**: セキュアなクロスオリジンアクセス
- **例外処理の強化**: エラーハンドリングの改善

#### 🛠️ Discord スキル

- **Claude Code Skills 対応**: `/agentic-vision-gemini` スキルで高度な画像分析をコマンド一つで実行可能

### バグ修正 / Bug Fixes

- **セキュリティ強化**: CORS設定と環境変数検証の改善
- **コード品質**: 玲子姐さんと美咲先輩によるレビュー反映
- **Dockerfile 改善**: cc-api に curl、google-genai を追加
- **ハンドラー修正**: スレッド取得を `fetch_channel` に変更

### インフラ変更 / Infrastructure Changes

- **Google API キー**: `.env.example` に `GOOGLE_API_KEY` を追加
- **Docker ボリューム**: ワークスペースとメディアディレクトリの設定を更新
- **Gitignore**: browser-api 関連と tmp フォルダを追加
- **テスト構成**: テストスイートを追加・再構成

### ドキュメント / Documentation

- **Agentic Vision README**: APIリファレンスとユースケースを更新
- **Browser API README**: セットアップ手順を追加
- **Discord Bot ドキュメント**: 返信機能と議論機能のドキュメント追加
- **テスト README**: パスを最新化

### テスト / Tests

- **Discord Bot テストスイート**: メッセージ返信、ファイル添付のテスト追加
- **ハンドラー個別テスト**: 各ハンドラーの単体テストと統合テスト

---

## English

### Overview

Cinderella v0.2.0 evolves image understanding and conversational AI experiences to the next level with the power of **Agentic Vision**.

Leveraging Gemini 3 Flash's cutting-edge vision capabilities, we now support autonomous image analysis via Think-Act-Observe loops, zoom-in inspection, annotation, and data visualization. The Discord Bot has evolved into a true conversational agent with file attachments, debate functionality, and message replies.

### What's New

#### 🔮 Agentic Vision

- **Gemini 3 Flash Preview Support**: Compatible with the latest Gemini 3 Flash model
- **Think-Act-Observe Loop**: Autonomous image understanding and task execution
- **Zoom-in Inspection**: Detailed analysis of high-resolution images
- **Annotation Features**: Bounding boxes and label rendering on images
- **Data Visualization**: Data extraction and plot generation from charts and graphs
- **Batch Analysis**: Process multiple images at once
- **Code Execution for Image Manipulation**: Dynamic image processing via Python execution environment

#### 🤖 Discord Bot Enhancements

- **File Attachment Support**: Analyze images by attaching them directly
- **Debate Feature**: Generate multi-perspective discussions with `!debate` command
- **Message Replies**: Reply to threads and manage conversation history
- **Mention Support**: Invoke with `@Cinderella`
- **Reaction Features**: Add reactions to messages
- **Improved Logging**: Detailed execution logs and debug information

#### 🌐 Browser API Service

- **New Service**: Added browser-api service to docker-compose
- **CORS Configuration**: Secure cross-origin access
- **Enhanced Exception Handling**: Improved error handling

#### 🛠️ Discord Skills

- **Claude Code Skills Support**: Execute advanced image analysis with `/agentic-vision-gemini` command

### Bug Fixes

- **Security Enhancements**: Improved CORS settings and environment variable validation
- **Code Quality**: Reflected reviews from Reiko and Misaki
- **Dockerfile Improvements**: Added curl and google-genai to cc-api
- **Handler Fixes**: Changed thread fetching to `fetch_channel`

### Infrastructure Changes

- **Google API Key**: Added `GOOGLE_API_KEY` to `.env.example`
- **Docker Volumes**: Updated workspace and media directory configurations
- **Gitignore**: Added browser-api related and tmp folders
- **Test Configuration**: Added and reorganized test suites

### Documentation

- **Agentic Vision README**: Updated API reference and use cases
- **Browser API README**: Added setup instructions
- **Discord Bot Documentation**: Added docs for reply and debate features
- **Test README**: Updated paths

### Tests

- **Discord Bot Test Suite**: Added tests for message replies and file attachments
- **Handler Unit Tests**: Individual and integration tests for each handler

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
