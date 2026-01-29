---
name: agentic-vision-gemini
description: |
  Gemini 3 Flash の Agentic Vision を活用した高度な画像分析・処理スキル。
  Think-Act-Observe ループによるエージェント的画像理解、コード実行による画像操作、
  ズームイン検査、アノテーション、ビジュアル数学・プロット生成をサポート。
  
  Use when: (1) 画像の細部を拡大・検査する必要がある時、(2) 画像にバウンディングボックスや
  ラベルを描画する時、(3) 表やグラフからデータを抽出・可視化する時、(4) 高解像度画像の
  詳細分析が必要な時、(5) 画像内のオブジェクトをカウント・計測する時、
  (6) Gemini API で画像分析タスクを自動化する時
---

# Agentic Vision in Gemini 3 Flash

Gemini 3 Flash の Agentic Vision は、静的な画像認識を能動的な調査プロセスに変換する。
視覚的推論とコード実行を組み合わせ、ズーム、検査、画像操作をステップバイステップで実行し、
視覚的証拠に基づいた回答を生成する。

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

client = genai.Client()

# 画像を読み込み
image = types.Part.from_uri(
    file_uri="https://example.com/image.jpg",
    mime_type="image/jpeg",
)

# Agentic Vision で分析（code_execution を有効化）
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "この画像の詳細を分析してください"],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)]
    ),
)
print(response.text)
```

## Agentic Vision の主要機能

### 1. ズーム・検査 (Zoom & Inspect)

細部を検出するとモデルが暗黙的にズームインする。高解像度入力に対して特に有効。

```python
# 詳細検査を促すプロンプト例
prompts = [
    "Zoom into the serial number and read it",
    "拡大してラベルのテキストを読み取って",
    "細部を確認して、全ての数字を抽出して"
]
```

### 2. 画像アノテーション (Image Annotation)

バウンディングボックスやラベルを描画して推論を視覚的に根拠付ける。

```python
# アノテーションを促すプロンプト例
prompts = [
    "Count the fingers and draw bounding boxes on each",
    "各オブジェクトにラベルを付けて",
    "検出した箇所をマークして"
]
```

### 3. ビジュアル数学・プロット (Visual Math & Plotting)

表やデータを解析し、Matplotlib/Python で可視化する。

```python
# データ可視化を促すプロンプト例
prompts = [
    "この表のデータを棒グラフにして",
    "Parse the table and create a line chart",
    "数値を計算してグラフで表示して"
]
```

## Workflow

1. **画像準備**: ローカルファイルまたはURLから画像を読み込み
2. **Code Execution 有効化**: `tools=[types.Tool(code_execution=...)]` を設定
3. **適切なプロンプト**: タスクに応じたプロンプトを選択（下記参照）
4. **結果検証**: モデルの出力と生成されたコード/画像を確認

## プロンプト設計ガイド

| タスク | プロンプトパターン |
|--------|-------------------|
| 細部読み取り | "Zoom into [対象] and [アクション]" |
| カウント | "Count [対象] and draw bounding boxes" |
| データ抽出 | "Parse the table and extract [データ]" |
| 可視化 | "Create a [グラフ種類] chart from [データソース]" |
| 比較分析 | "Compare [A] and [B], annotate differences" |

## 詳細リファレンス

- **API詳細・設定オプション**: [references/api_reference.md](references/api_reference.md)
- **実践的ユースケース集**: [references/use_cases.md](references/use_cases.md)

## スクリプト

- `scripts/agentic_vision.py`: 基本的なAgentic Vision API呼び出し
- `scripts/image_utils.py`: 画像の前処理・後処理ユーティリティ
- `scripts/batch_analyze.py`: 複数画像のバッチ分析

## Tips

- **暗黙的ズーム**: 「詳細を見て」「拡大して」などのプロンプトでズームが自動発動
- **明示的トリガー**: 回転やプロット生成は現時点では明示的プロンプトが必要
- **高解像度画像**: 解像度が高いほど細部検査の精度が向上
- **ビジョンベンチマーク**: Code Execution有効化で5-10%の品質向上
