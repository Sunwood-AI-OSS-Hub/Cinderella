<div align="center">

# Agentic Vision Gemini Skill

<a href="README_JA.md"><img src="https://img.shields.io/badge/%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88-%E6%97%A5%E6%9C%AC%E8%AA%9E-white.svg" alt="JA doc"/></a>
<a href="README.md"><img src="https://img.shields.io/badge/Documentation-English-white.svg" alt="EN doc"/></a>

</div>

## 概要

Agentic Vision Gemini Skill は、Gemini 3 Flash の Agentic Vision 機能を活用した高度な画像分析・処理スキルです。Think-Act-Observe ループによる反復的な分析、ズーム・検査機能、アノテーション作成、ビジュアル数学などをサポートします。

## 特徴

- **Think-Act-Observe ループ**: 反復的な画像分析プロセス
- **ズーム・検査機能**: 画像の細部を拡大して詳細に確認
- **アノテーション作成**: バウンディングボックスやラベルを描画
- **ビジュアル数学**: 表やグラフからデータを抽出・可視化

## クイックスタート

詳細な使用方法については [SKILL.md](SKILL.md) を参照してください。

## スクリプト

| スクリプト | 説明 |
|-----------|------|
| `scripts/agentic_vision.py` | Agentic Vision の基本的な使用例 |
| `scripts/batch_analyze.py` | 複数画像の一括分析 |
| `scripts/image_utils.py` | 画像の前処理・後処理ユーティリティ |

## リファレンス

- [API リファレンス](references/api_reference.md) - API 詳細・設定オプション
- [ユースケース](references/use_cases.md) - 実践的な使用例

## Agentic Vision の主要機能

### 1. ズーム・検査 (Zoom & Inspect)

細部を検出するとモデルが暗黙的にズームインします。高解像度入力に対して特に有効です。

**使用例:**
```bash
# 詳細検査を促すプロンプト例
"Zoom into the serial number and read it"
"拡大してラベルのテキストを読み取って"
"細部を確認して、全ての数字を抽出して"
```

### 2. 画像アノテーション (Image Annotation)

バウンディングボックスやラベルを描画して推論を視覚的に根拠付けます。

**使用例:**
```bash
# アノテーションを促すプロンプト例
"Count the fingers and draw bounding boxes on each"
"各オブジェクトにラベルを付けて"
"検出した箇所をマークして"
```

### 3. ビジュアル数学・プロット (Visual Math & Plotting)

表やデータを解析し、Matplotlib/Python で可視化します。

**使用例:**
```bash
# データ可視化を促すプロンプト例
"この表のデータを棒グラフにして"
"Parse the table and create a line chart"
"数値を計算してグラフで表示して"
```

## コアコンセプト: Think-Act-Observe ループ

```
Think  → 画像とクエリを分析し、マルチステップ計画を立案
Act    → Python コードを生成・実行して画像を操作・分析
Observe → 変換された画像をコンテキストに追加し、結果を検査
```

## 基本的な使用方法

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

## プロンプト設計ガイド

| タスク | プロンプトパターン |
|--------|-------------------|
| 細部読み取り | "Zoom into [対象] and [アクション]" |
| カウント | "Count [対象] and draw bounding boxes" |
| データ抽出 | "Parse the table and extract [データ]" |
| 可視化 | "Create a [グラフ種類] chart from [データソース]" |
| 比較分析 | "Compare [A] and [B], annotate differences" |

## Tips

- **暗黙的ズーム**: 「詳細を見て」「拡大して」などのプロンプトでズームが自動発動
- **明示的トリガー**: 回転やプロット生成は現時点では明示的プロンプトが必要
- **高解像度画像**: 解像度が高いほど細部検査の精度が向上
- **ビジョンベンチマーク**: Code Execution 有効化で 5-10% の品質向上

## 使用すべきタイミング

このスキルは以下の場合に使用してください：

1. 画像の細部を拡大・検査する必要がある時
2. 画像にバウンディングボックスやラベルを描画する時
3. 表やグラフからデータを抽出・可視化する時
4. 高解像度画像の詳細分析が必要な時
5. 画像内のオブジェクトをカウント・計測する時
6. Gemini API で画像分析タスクを自動化する時

## ライセンス

MIT License
