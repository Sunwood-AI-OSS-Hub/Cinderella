# Agentic Vision ユースケース集

## Table of Contents

1. [ズーム・検査ユースケース](#ズーム検査ユースケース)
2. [画像アノテーション](#画像アノテーション)
3. [ビジュアル数学・プロット](#ビジュアル数学プロット)
4. [ドキュメント処理](#ドキュメント処理)
5. [品質検査・コンプライアンス](#品質検査コンプライアンス)
6. [複合タスク](#複合タスク)

---

## ズーム・検査ユースケース

### シリアル番号の読み取り

```python
from google import genai
from google.genai import types
import os

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    ),
)

# 画像を読み込み
with open("product.jpg", "rb") as f:
    image_data = f.read()
image = types.Part.from_bytes(data=image_data, mime_type="image/jpeg")

response = chat.send_message([
    image,
    "Zoom into any serial numbers or product codes visible in this image. "
    "Read and transcribe all alphanumeric codes you find."
])

print(response.text)
```

**モデルの動作**: クロップコードを生成し、シリアル番号領域を拡大して再分析

### 遠くの看板・標識の読み取り

```python
response = chat.send_message([
    image,
    "この画像に写っている看板や標識のテキストを全て読み取ってください。"
    "遠くにあるものも拡大して確認してください。"
])
```

### 細部の比較検査

```python
response = chat.send_message([
    image,
    "Compare the left and right halves of this image. "
    "Zoom into areas with differences and annotate them."
])
```

---

## 画像アノテーション

### オブジェクトカウント

```python
response = chat.send_message([
    image,
    "Count the fingers shown in this image. "
    "Draw a bounding box around each finger and label them with numbers. "
    "This ensures accurate counting."
])
```

**モデルの動作**: Pythonで描画コードを生成し、バウンディングボックスと数字ラベルを描画

### 物体検出とバウンディングボックス

```python
response = chat.send_message([
    image,
    "画像内のオブジェクトを検出して、バウンディングボックスを描画してください。"
    "検出した各オブジェクトにラベルを付けてください。"
])
```

出力例:
```json
[
  {"box_2d": [222, 80, 508, 298], "label": "stapler"},
  {"box_2d": [244, 281, 396, 440], "label": "pencil"}
]
```

**注意**: Gemini の `box_2d` は `[ymin, xmin, ymax, xmax]` 形式の正規化座標（0-1000）

### 欠陥検出とマーキング

```python
response = chat.send_message([
    image,
    "この製品画像を検査し、傷や欠陥を見つけてください。"
    "見つけた箇所に赤い円でマークし、欠陥の種類をラベル付けしてください。"
])
```

---

## ビジュアル数学・プロット

### 表からグラフ生成

```python
response = chat.send_message([
    image,
    "Parse the data table in this image. "
    "Create a bar chart comparing all values. "
    "Normalize the baseline to 1.0 for easy comparison."
])
```

**モデルの動作**:
1. 表データを解析・抽出
2. Matplotlib コードを生成
3. 正規化した棒グラフを作成

### 数学的計算と可視化

```python
response = chat.send_message([
    image,
    "この画像に含まれる数式を読み取り、計算してください。"
    "結果をグラフで可視化してください。"
])
```

### 財務データの分析

```python
response = chat.send_message([
    image,
    "Extract the financial data from this quarterly report image. "
    "Create a line chart showing the trend over time. "
    "Add annotations for significant changes (>10%)."
])
```

---

## ドキュメント処理

### 建築図面の検証

```python
response = chat.send_message([
    image,
    "Analyze this building plan for code compliance.\n"
    "1. Zoom into roof edges and verify setback requirements\n"
    "2. Check window-to-wall ratios for each section\n"
    "3. Annotate any potential violations"
])
```

### 手書き文書の解読

```python
response = chat.send_message([
    image,
    "この手書きメモの内容を読み取ってください。"
    "読みにくい部分は拡大して確認してください。"
])
```

### フォーム入力検証

```python
response = chat.send_message([
    image,
    "Verify that all required fields in this form are filled. "
    "Highlight any empty or incomplete fields. "
    "Check for common errors (e.g., date formats, signatures)."
])
```

---

## 品質検査・コンプライアンス

### 製品ラベル検証

```python
response = chat.send_message([
    image,
    "Inspect this product label:\n"
    "1. Zoom into the nutrition facts and verify all values are legible\n"
    "2. Check expiration date format\n"
    "3. Verify barcode quality\n"
    "4. List any compliance issues found"
])
```

---

## 複合タスク

### データ抽出→計算→可視化パイプライン

```python
response = chat.send_message([
    image,
    """Complete analysis pipeline for this chart image:

1. EXTRACT: Parse all data points from the chart
2. CALCULATE: Compute year-over-year growth rates
3. VISUALIZE: Create a new chart showing growth trends
4. ANNOTATE: Mark peak and trough points

Output both the analysis and the new visualization."""
])
```

### マルチターン探索

```python
# チャットセッションで複数回のやり取り
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    ),
)

# 1回目: 全体の分析
response1 = chat.send_message([image, "この画像で最も重要な領域を特定して"])
print(response1.text)

# 2回目: 詳細分析
response2 = chat.send_message("その領域をさらに詳しく分析して")
print(response2.text)
```

---

## プロンプトテンプレート集

### 汎用詳細分析テンプレート

```python
DETAIL_ANALYSIS_TEMPLATE = """
Analyze this image with the following approach:

1. Initial Overview: Describe what you see at first glance
2. Detail Inspection: Zoom into {target_areas} for closer examination
3. Data Extraction: Extract any {data_types} present
4. Visualization: Create {visualization_type} to summarize findings
5. Summary: Provide key insights and recommendations

Focus particularly on: {focus_areas}
"""
```

### 品質検査テンプレート

```python
QA_INSPECTION_TEMPLATE = """
Quality Inspection Protocol:

□ Visual Defects: Scan for scratches, dents, discoloration
□ Label Accuracy: Verify all text is correct and legible
□ Dimensional Check: Measure visible dimensions if scale is present
□ Compliance: Check against {standards}

For each issue found:
- Draw bounding box
- Label with defect type
- Rate severity (1-5)
"""
```

---

## バウンディングボックスの処理

### Gemini からの座標を描画

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

---

## 思考レベルの使い分け

| タスク | 推奨レベル | 理由 |
|--------|-----------|------|
| 単純な物体検出 | LOW | 高速処理 |
| 一般的な画像分析 | MEDIUM | バランス取れた推論 |
| 複雑な比較分析 | HIGH | 深い推論が必要 |
| 複数のステップが必要なタスク | HIGH | Think-Act-Observe ループを最大活用 |

```python
# 複雑なタスクでは HIGH を使用
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    ),
)
```
