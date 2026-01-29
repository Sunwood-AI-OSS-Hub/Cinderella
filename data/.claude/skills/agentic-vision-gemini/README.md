<div align="center">

# Agentic Vision Gemini Skill

<a href="README_JA.md"><img src="https://img.shields.io/badge/%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88-%E6%97%A5%E6%9C%AC%E8%AA%9E-white.svg" alt="JA doc"/></a>
<a href="README.md"><img src="https://img.shields.io/badge/Documentation-English-white.svg" alt="EN doc"/></a>

</div>

## Overview

Agentic Vision Gemini Skill is an advanced image analysis and processing skill leveraging Gemini 3 Flash's Agentic Vision capabilities. It supports Think-Act-Observe loop for iterative analysis, zoom and inspection features, annotation creation, and visual mathematics.

## Features

- **Think-Act-Observe Loop**: Iterative image analysis process
- **Zoom & Inspection**: Zoom into image details for close examination
- **Annotation Creation**: Draw bounding boxes and labels
- **Visual Mathematics**: Extract and visualize data from tables and charts

## Quick Start

See [SKILL.md](SKILL.md) for detailed usage instructions.

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/agentic_vision.py` | Basic Agentic Vision usage examples |
| `scripts/batch_analyze.py` | Batch image analysis |
| `scripts/image_utils.py` | Image preprocessing and postprocessing utilities |

## References

- [API Reference](references/api_reference.md) - API details and configuration options
- [Use Cases](references/use_cases.md) - Practical usage examples

## Key Features of Agentic Vision

### 1. Zoom & Inspect

The model automatically zooms in when detecting fine details. Particularly effective for high-resolution inputs.

**Example usage:**
```bash
# Example prompts for detailed inspection
"Zoom into the serial number and read it"
"拡大してラベルのテキストを読み取って"
"細部を確認して、全ての数字を抽出して"
```

### 2. Image Annotation

Draw bounding boxes and labels to visually ground reasoning.

**Example usage:**
```bash
# Example prompts for annotation
"Count the fingers and draw bounding boxes on each"
"各オブジェクトにラベルを付けて"
"検出した箇所をマークして"
```

### 3. Visual Math & Plotting

Parse tables and data, then visualize with Matplotlib/Python.

**Example usage:**
```bash
# Example prompts for data visualization
"この表のデータを棒グラフにして"
"Parse the table and create a line chart"
"数値を計算してグラフで表示して"
```

## Core Concept: Think-Act-Observe Loop

```
Think   → Analyze image and query, formulate multi-step plan
Act     → Generate and execute Python code to manipulate/analyze image
Observe → Add transformed image to context, inspect results
```

## Basic Usage

```python
from google import genai
from google.genai import types

client = genai.Client()

# Load image
image = types.Part.from_uri(
    file_uri="https://example.com/image.jpg",
    mime_type="image/jpeg",
)

# Analyze with Agentic Vision (enable code_execution)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "この画像の詳細を分析してください"],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)]
    ),
)
print(response.text)
```

## Prompt Design Guide

| Task | Prompt Pattern |
|------|----------------|
| Fine detail reading | "Zoom into [object] and [action]" |
| Counting | "Count [object] and draw bounding boxes" |
| Data extraction | "Parse the table and extract [data]" |
| Visualization | "Create a [chart type] chart from [data source]" |
| Comparative analysis | "Compare [A] and [B], annotate differences" |

## Tips

- **Implicit Zoom**: Prompts like "look at details" or "zoom in" automatically trigger zoom
- **Explicit Triggers**: Rotation and plot generation currently require explicit prompts
- **High-Resolution Images**: Higher resolution improves detail inspection accuracy
- **Vision Benchmarks**: Code Execution improves quality by 5-10%

## When to Use

Use this skill when:

1. You need to zoom into and inspect fine details of an image
2. You need to draw bounding boxes or labels on images
3. You need to extract and visualize data from tables or charts
4. You need detailed analysis of high-resolution images
5. You need to count or measure objects in images
6. You need to automate image analysis tasks with Gemini API

## License

MIT License
