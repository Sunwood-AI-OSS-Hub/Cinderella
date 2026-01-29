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
prompt = """
Zoom into any serial numbers or product codes visible in this image.
Read and transcribe all alphanumeric codes you find.
"""

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, prompt],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)]
    ),
)
```

**モデルの動作**: クロップコードを生成し、シリアル番号領域を拡大して再分析

### 遠くの看板・標識の読み取り

```python
prompt = """
この画像に写っている看板や標識のテキストを全て読み取ってください。
遠くにあるものも拡大して確認してください。
"""
```

### 細部の比較検査

```python
prompt = """
Compare the left and right halves of this image.
Zoom into areas with differences and annotate them.
"""
```

---

## 画像アノテーション

### オブジェクトカウント（指のカウント例）

```python
prompt = """
Count the fingers shown in this image.
Draw a bounding box around each finger and label them with numbers.
This ensures accurate counting.
"""
```

**モデルの動作**: Pythonで描画コードを生成し、バウンディングボックスと数字ラベルを描画

### 検出結果の可視化

```python
prompt = """
Identify all faces in this image.
Draw bounding boxes around each face with confidence scores.
Use different colors for different expressions if detectable.
"""
```

### 欠陥検出とマーキング

```python
prompt = """
この製品画像を検査し、傷や欠陥を見つけてください。
見つけた箇所に赤い円でマークし、欠陥の種類をラベル付けしてください。
"""
```

---

## ビジュアル数学・プロット

### 表からグラフ生成

```python
prompt = """
Parse the data table in this image.
Create a bar chart comparing all values.
Normalize the baseline to 1.0 for easy comparison.
"""
```

**モデルの動作**: 
1. 表データを解析・抽出
2. Matplotlib コードを生成
3. 正規化した棒グラフを作成

### 数学的計算と可視化

```python
prompt = """
この画像に含まれる数式を読み取り、計算してください。
結果をグラフで可視化してください。
"""
```

### 財務データの分析

```python
prompt = """
Extract the financial data from this quarterly report image.
Create a line chart showing the trend over time.
Add annotations for significant changes (>10%).
"""
```

---

## ドキュメント処理

### 建築図面の検証（PlanCheckSolver 例）

```python
prompt = """
Analyze this building plan for code compliance.
1. Zoom into roof edges and verify setback requirements
2. Check window-to-wall ratios for each section
3. Annotate any potential violations
"""
```

**実績**: 高解像度入力の反復検査により精度が5%向上

### 手書き文書の解読

```python
prompt = """
この手書きメモの内容を読み取ってください。
読みにくい部分は拡大して確認してください。
"""
```

### フォーム入力検証

```python
prompt = """
Verify that all required fields in this form are filled.
Highlight any empty or incomplete fields.
Check for common errors (e.g., date formats, signatures).
"""
```

---

## 品質検査・コンプライアンス

### 製品ラベル検証

```python
prompt = """
Inspect this product label:
1. Zoom into the nutrition facts and verify all values are legible
2. Check expiration date format
3. Verify barcode quality
4. List any compliance issues found
"""
```

### 医療画像の詳細検査

```python
prompt = """
Analyze this X-ray image:
1. Identify regions of interest
2. Zoom into suspicious areas for detailed inspection
3. Annotate findings with bounding boxes
4. Provide confidence levels for each finding

Note: This is for educational purposes only.
"""
```

---

## 複合タスク

### データ抽出→計算→可視化パイプライン

```python
prompt = """
Complete analysis pipeline for this chart image:

1. EXTRACT: Parse all data points from the chart
2. CALCULATE: Compute year-over-year growth rates
3. VISUALIZE: Create a new chart showing growth trends
4. ANNOTATE: Mark peak and trough points

Output both the analysis and the new visualization.
"""
```

### 比較分析レポート

```python
prompt = """
Compare these two product images side by side:

1. Zoom into each product's label
2. Extract key specifications
3. Create a comparison table
4. Generate a visualization highlighting differences
5. Summarize recommendations
"""
```

### インタラクティブ探索

```python
# マルチターンでの探索的分析
messages = [
    {"role": "user", "content": [image, "この画像で最も重要な領域を特定して"]}
]

response1 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=messages,
    config=config,
)

# 続けて詳細分析
messages.append({"role": "model", "content": response1.text})
messages.append({"role": "user", "content": "その領域をさらに詳しく分析して"})

response2 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=messages,
    config=config,
)
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
