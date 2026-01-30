---
name: agentic-vision-gemini
description: |
  Gemini 3 Flash (gemini-3-flash-preview) の Agentic Vision を活用した高度な画像分析・処理スキル。
  Think-Act-Observe ループによるエージェント的画像理解、コード実行による画像操作、
  ズームイン検査、アノテーション、ビジュアル数学・プロット生成をサポート。

  Use when: (1) 画像の細部を拡大・検査する必要がある時、(2) 画像にバウンディングボックスや
  ラベルを描画する時、(3) 表やグラフからデータを抽出・可視化する時、(4) 高解像度画像の
  詳細分析が必要な時、(5) 画像内のオブジェクトをカウント・計測する時、
  (6) Gemini API で画像分析タスクを自動化する時

  環境変数: GOOGLE_API_KEY が必要（https://ai.google.dev/ で取得）
---

# Agentic Vision in Gemini 3 Flash

Gemini 3 Flash (`gemini-3-flash-preview`) の Agentic Vision は、静的な画像認識を能動的な調査プロセスに変換する。
視覚的推論とコード実行を組み合わせ、ズーム、検査、画像操作をステップバイステップで実行し、視覚的証拠に基づいた回答を生成する。

## Core Concept: Think-Act-Observe Loop

```
Think → 画像とクエリを分析し、マルチステップ計画を立案
Act   → Python コードを生成・実行して画像を操作・分析
Observe → 変換された画像をコンテキストに追加し、結果を検査
```

## Quick Start

```python
from google import genai
from google.genai import types
import os

# APIキーを設定（環境変数 GOOGLE_API_KEY が必要）
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# チャットセッションを作成（推奨）
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    ),
)

# ローカル画像を読み込んで分析
image_path = "/path/to/image.png"
with open(image_path, "rb") as f:
    image_data = f.read()

response = chat.send_message(
    message=[
        types.Part.from_bytes(
            data=image_data,
            mime_type="image/png",  # または "image/jpeg"
        ),
        "画像内のオブジェクトを検出して、バウンディングボックスを描画してください。"
    ]
)

print(response.text)
```

## 必要な設定

### 1. APIキーの取得
- https://ai.google.dev/ で Google Cloud プロジェクトを作成
- Gemini API を有効化
- APIキーを取得

### 2. 環境変数の設定
```bash
# .env または環境変数に設定
export GOOGLE_API_KEY=your_api_key_here
```

### 3. google-genai パッケージのインストール
```bash
pip install google-genai
# または
uv pip install google-genai
```

### 4. 画像描画用パッケージ（オプション）
```bash
pip install Pillow
```

## Agentic Vision の主要機能

### 1. 物体検出とバウンディングボックス

Agentic Vision の code_execution 機能を使うと、自動的に Python コードを生成・実行して物体検出を行います。

```python
response = chat.send_message(
    message=[
        types.Part.from_bytes(data=image_data, mime_type="image/png"),
        "画像内のオブジェクトを検出して、バウンディングボックスを描画してください。"
    ]
)
# 出力例: [{"box_2d": [ymin, xmin, ymax, xmax], "label": "calculator"}, ...]
```

**重要**: Gemini の `box_2d` は `[ymin, xmin, ymax, xmax]` 形式の**正規化座標（0-1000）**です。

### 2. オブジェクトカウント

画像内のオブジェクトを数え上げ、カテゴリ別に集計します。

```python
response = chat.send_message(
    message=[
        types.Part.from_bytes(data=image_data, mime_type="image/png"),
        "画像内のオブジェクトを数えて、各カテゴリの個数を報告してください。"
    ]
)
# 出力例: ホッチキス: 1個, ハサミ: 1挺, 電卓: 1台, 鉛筆: 3本, ...
```

### 3. ズーム・詳細検査 (Zoom & Inspect)

高解像度画像の細部を検出すると、モデルが暗黙的にズームインして詳細を確認します。

```python
# 詳細検査を促すプロンプト例
prompts = [
    "拡大してラベルのテキストを読み取って",
    "細部を確認して、全ての数字を抽出して",
    "シリアルナンバーを読み取って"
]
```

### 4. ビジュアル数学・プロット (Visual Math & Plotting)

表やデータを解析し、Matplotlib/Python で可視化します。

```python
prompts = [
    "この表のデータを棒グラフにして",
    "数値を計算してグラフで表示して",
    "データを抽出して可視化して"
]
```

## 設定オプション

### thinking_config

思考レベルを設定して、Agentic Vision の推論深度を調整します。

```python
thinking_config=types.ThinkingConfig(thinking_level="MEDIUM")
# 設定値: "LOW", "MEDIUM", "HIGH"
```

| レベル | 説明 | 用途 |
|--------|------|------|
| LOW | 軽量な推論、高速レスポンス | 単純な物体検出 |
| MEDIUM | バランスの取れた推論（推奨） | 一般的な画像分析 |
| HIGH | 深い推論、複雑なタスク向け | 複雑な比較分析、詳細検査 |

### code_execution

必須設定。Agentic Vision の核心機能です。

```python
tools=[types.Tool(code_execution=types.ToolCodeExecution)]
```

## Workflow

1. **チャットセッション作成**: `client.chats.create()` でセッションを作成（推奨）
2. **画像読み込み**: `Part.from_bytes()` でローカル画像を読み込み
3. **プロンプト送信**: `chat.send_message()` で分析リクエスト
4. **結果確認**: `response.text` で結果、`candidates` で実行されたコードを確認

## プロンプト設計ガイド

| タスク | プロンプトパターン |
|--------|-------------------|
| 物体検出 | "画像内のオブジェクトを検出して、バウンディングボックスを描画してください" |
| カウント | "画像内の[対象]を数えて、各カテゴリの個数を報告してください" |
| 細部読み取り | "拡大して[対象]のテキストを読み取って" |
| データ抽出 | "表のデータを抽出してください" |
| 可視化 | "データをグラフに可視化してください" |
| 比較分析 | "[A]と[B]を比較して、差異をアノテートしてください" |

## 実行結果の確認

Code Execution の結果を確認する方法：

```python
response = chat.send_message(...)

# テキスト結果
print(response.text)

# 実行されたコードやコード実行結果を確認
if hasattr(response, 'candidates') and response.candidates:
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'executable') and part.executable:
            print("Code executed!")

        if hasattr(part, 'code_execution_result') and part.code_execution_result:
            print("Execution output:", part.code_execution_result.output)

        if hasattr(part, 'inline_data') and part.inline_data:
            print("Generated image:", part.inline_data.mime_type)
```

## バウンディングボックスの描画

Gemini から取得した正規化座標を使って画像を描画する方法：

### image_utils.py を使用

```python
from image_utils import draw_bounding_boxes

# Gemini code_execution の出力から抽出した座標
# [ymin, xmin, ymax, xmax] - 0-1000の正規化座標
boxes = [
    (222, 80, 508, 298),   # stapler
    (244, 281, 396, 440),  # pencil
]

labels = ["stapler", "pencil"]

# 描画（正規化座標、yxyx形式）
draw_bounding_boxes(
    'input.png',
    'output.png',
    boxes=boxes,
    labels=labels,
    normalized=True,
    normalized_max=1000,
    box_format="yxyx"
)
```

### 座標形式の説明

| 形式 | 説明 | 例 |
|------|------|-----|
| yxyx | Geminiの出力 `[ymin, xmin, ymax, xmax]` (0-1000) | `(222, 80, 508, 298)` |
| xyxy | 一般的な形式 `[x1, y1, x2, y2]` | `(80, 222, 298, 508)` |

## スクリプトの使用方法

### agentic_vision.py - 単一画像の分析

```bash
# 環境変数を設定
export GOOGLE_API_KEY=your_api_key

# 物体検出
python agentic_vision.py image.jpg "画像内のオブジェクトを検出してバウンディングボックスを描画して"

# オブジェクトカウント
python agentic_vision.py image.png "画像内のオブジェクトを数えて各カテゴリの個数を報告して"

# JSON出力
python agentic_vision.py image.jpg "分析して" --json

# 思考レベルを指定
python agentic_vision.py image.jpg "詳細分析" --thinking HIGH
```

### batch_analyze.py - 複数画像の一括分析

```bash
# ディレクトリ内の全画像を分析
python batch_analyze.py -d ./images -p "画像を説明して"

# 画像リストファイルから読み込み
python batch_analyze.py -l images.txt -p "オブジェクトを検出して"

# 結果をJSONで保存
python batch_analyze.py -d ./images -p "物体を数えて" -o results.json

# 思考レベルをHIGHに設定
python batch_analyze.py -d ./images -p "詳細分析" --thinking HIGH
```

### image_utils.py - 画像処理ユーティリティ

```bash
# 画像情報を表示
python image_utils.py image.png

# バウンディングボックス描画（Pythonから）
python -c "
from image_utils import draw_bounding_boxes
draw_bounding_boxes('input.png', 'output.png',
                   boxes=[(222, 80, 508, 298)],
                   labels=['stapler'],
                   normalized=True, normalized_max=1000, box_format='yxyx')
"
```

## スクリプト

- `scripts/agentic_vision.py`: 基本的なAgentic Vision API呼び出し
- `scripts/batch_analyze.py`: 複数画像のバッチ分析
- `scripts/image_utils.py`: 画像の前処理・後処理ユーティリティ

## 詳細リファレンス

- **API詳細・設定オプション**: [references/api_reference.md](references/api_reference.md)
- **実践的ユースケース集**: [references/use_cases.md](references/use_cases.md)

## 注意点

- **モデル**: `gemini-3-flash-preview` を使用してください
- **環境変数**: `GOOGLE_API_KEY` が必須です
- **チャットセッション**: `client.chats.create()` の使用を推奨します（コンテキスト保持のため）
- **画像サイズ**: 大きな画像の場合は適切に処理されますが、APIリミットに注意してください
- **座標形式**: Gemini の `box_2d` は `[ymin, xmin, ymax, xmax]` (0-1000) の正規化座標です

## Tips

- **暗黙的ズーム**: 「詳細を見て」「拡大して」などのプロンプトでズームが自動発動
- **バウンディングボックス**: 「検出して」「マークして」で自動的に code_execution が動作
- **高解像度画像**: 解像度が高いほど細部検査の精度が向上
- **思考レベル**: 複雑なタスクでは `thinking_level="HIGH"` を検討
- **マルチターン**: チャットセッションで複数回のやり取りが可能
