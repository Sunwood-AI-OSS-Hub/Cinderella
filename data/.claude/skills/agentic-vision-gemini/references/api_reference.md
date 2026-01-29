# Agentic Vision API Reference

## Table of Contents

1. [クライアント初期化](#クライアント初期化)
2. [画像入力方法](#画像入力方法)
3. [Code Execution 設定](#code-execution-設定)
4. [レスポンス構造](#レスポンス構造)
5. [エラーハンドリング](#エラーハンドリング)
6. [高度な設定オプション](#高度な設定オプション)

---

## クライアント初期化

```python
from google import genai
from google.genai import types

# 基本的な初期化（環境変数 GOOGLE_API_KEY を使用）
client = genai.Client()

# API キーを明示的に指定
client = genai.Client(api_key="YOUR_API_KEY")

# Vertex AI を使用する場合
client = genai.Client(
    vertexai=True,
    project="your-project-id",
    location="us-central1"
)
```

## 画像入力方法

### URL から読み込み

```python
image = types.Part.from_uri(
    file_uri="https://example.com/image.jpg",
    mime_type="image/jpeg",
)
```

### ローカルファイルから読み込み

```python
import base64
from pathlib import Path

def load_image_from_file(path: str) -> types.Part:
    """ローカルファイルから画像を読み込む"""
    file_path = Path(path)
    mime_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }.get(file_path.suffix.lower(), 'image/jpeg')
    
    with open(file_path, 'rb') as f:
        data = base64.standard_b64encode(f.read()).decode('utf-8')
    
    return types.Part.from_bytes(data=data, mime_type=mime_type)
```

### Base64 エンコード済みデータから

```python
image = types.Part.from_bytes(
    data=base64_encoded_string,
    mime_type="image/png"
)
```

### サポートされる MIME タイプ

| MIME Type | 拡張子 |
|-----------|--------|
| `image/jpeg` | .jpg, .jpeg |
| `image/png` | .png |
| `image/gif` | .gif |
| `image/webp` | .webp |

## Code Execution 設定

### 基本設定

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(code_execution=types.ToolCodeExecution)]
)

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "プロンプト"],
    config=config,
)
```

### 複数ツールの組み合わせ

```python
config = types.GenerateContentConfig(
    tools=[
        types.Tool(code_execution=types.ToolCodeExecution),
        # 他のツールも追加可能
    ]
)
```

## レスポンス構造

### テキストレスポンス

```python
print(response.text)  # 最終的なテキスト出力
```

### 詳細なレスポンス解析

```python
for candidate in response.candidates:
    for part in candidate.content.parts:
        if hasattr(part, 'text'):
            print(f"Text: {part.text}")
        if hasattr(part, 'executable_code'):
            print(f"Code: {part.executable_code.code}")
        if hasattr(part, 'code_execution_result'):
            print(f"Result: {part.code_execution_result.output}")
```

### コード実行結果の抽出

```python
def extract_code_and_results(response):
    """レスポンスからコードと実行結果を抽出"""
    results = {
        'text': [],
        'code': [],
        'execution_results': [],
        'images': []
    }
    
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                results['text'].append(part.text)
            if hasattr(part, 'executable_code'):
                results['code'].append(part.executable_code.code)
            if hasattr(part, 'code_execution_result'):
                results['execution_results'].append(
                    part.code_execution_result.output
                )
            if hasattr(part, 'inline_data'):
                results['images'].append(part.inline_data)
    
    return results
```

## エラーハンドリング

```python
from google.api_core import exceptions

try:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[image, prompt],
        config=config,
    )
except exceptions.InvalidArgument as e:
    print(f"無効な引数: {e}")
except exceptions.ResourceExhausted as e:
    print(f"レート制限: {e}")
except exceptions.GoogleAPIError as e:
    print(f"API エラー: {e}")
```

## 高度な設定オプション

### 生成パラメータ

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
    temperature=0.7,          # 創造性（0.0-2.0）
    top_p=0.95,              # 確率的サンプリング
    top_k=40,                # 上位k個のトークン
    max_output_tokens=8192,  # 最大出力トークン
    stop_sequences=["END"],  # 停止シーケンス
)
```

### Safety Settings

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
    safety_settings=[
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE"
        ),
    ]
)
```

### システムインストラクション

```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, prompt],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        system_instruction="あなたは画像分析の専門家です。詳細かつ正確な分析を行ってください。"
    ),
)
```

## モデル名

| モデル | 用途 |
|--------|------|
| `gemini-3-flash-preview` | Agentic Vision 対応（推奨） |
| `gemini-2.0-flash` | 高速処理 |
| `gemini-1.5-pro` | 長いコンテキスト |

## API エンドポイント

- **Google AI Studio**: `https://generativelanguage.googleapis.com/`
- **Vertex AI**: リージョンベースのエンドポイント
