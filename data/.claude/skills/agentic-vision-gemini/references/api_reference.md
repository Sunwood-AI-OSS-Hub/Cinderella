# Agentic Vision API Reference

## Table of Contents

1. [クライアント初期化](#クライアント初期化)
2. [チャットセッション](#チャットセッション)
3. [画像入力方法](#画像入力方法)
4. [設定オプション](#設定オプション)
5. [レスポンス構造](#レスポンス構造)
6. [エラーハンドリング](#エラーハンドリング)

---

## クライアント初期化

```python
from google import genai
from google.genai import types
import os

# APIキーを環境変数から取得（推奨）
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# 環境変数 GOOGLE_API_KEY が設定されている場合は省略可能
# client = genai.Client()
```

**APIキーの取得**: https://ai.google.dev/

## チャットセッション

Agentic Vision ではチャットセッションの使用を推奨します。

```python
# チャットセッションを作成
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    ),
)

# メッセージを送信
response = chat.send_message(
    message=[image, "プロンプト"]
)
```

### チャットセッションの利点

- **コンテキスト保持**: 複数のメッセージ間でコンテキストが維持される
- **追加入力**: 同じセッションで追加の分析リクエストが可能
- **効率的**: 再度 code_execution 設定をする必要がない

### マルチターンの例

```python
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    ),
)

# 1回目: 全体の分析
response1 = chat.send_message([image, "この画像を全体を説明して"])
print(response1.text)

# 2回目: 詳細な検査
response2 = chat.send_message("左側にあるオブジェクトの詳細を説明して")
print(response2.text)
```

## 画像入力方法

### ローカルファイルから読み込み（推奨）

```python
from pathlib import Path

image_path = "/path/to/image.png"

# MIMEタイプの判定
mime_type = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
}.get(Path(image_path).suffix.lower(), 'image/jpeg')

# 生バイナリデータを読み込む
with open(image_path, 'rb') as f:
    image_data = f.read()

image = types.Part.from_bytes(data=image_data, mime_type=mime_type)
```

### Base64 エンコード済みデータ

```python
import base64

# Base64 エンコードされた文字列がある場合
base64_data = "iVBORw0KGgoAAAANSUhEUg..."
image = types.Part.from_bytes(
    data=base64.b64decode(base64_data),
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

## 設定オプション

### code_execution（必須）

Agentic Vision の核心機能。Python コードの生成・実行を有効にします。

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(code_execution=types.ToolCodeExecution)]
)
```

### thinking_config

思考レベルを設定して、Agentic Vision の推論深度を調整します。

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
    thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
)
```

| レベル | 説明 | 用途 |
|--------|------|------|
| LOW | 軽量な推論、高速レスポンス | 単純なタスク |
| MEDIUM | バランスの取れた推論（推奨） | 一般的な画像分析 |
| HIGH | 深い推論、複雑なタスク向け | 複雑な物体検出、詳細分析 |

### 生成パラメータ

```python
config = types.GenerateContentConfig(
    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
    thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    temperature=0.7,          # 創造性（0.0-2.0）
    top_p=0.95,              # 確率的サンプリング
    top_k=40,                # 上位k個のトークン
    max_output_tokens=8192,  # 最大出力トークン
)
```

### システムインストラクション

```python
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
        system_instruction="あなたは画像分析の専門家です。詳細かつ正確な分析を行ってください。"
    ),
)
```

## レスポンス構造

### テキストレスポンス

```python
# 最終的なテキスト出力
print(response.text)
```

### 詳細なレスポンス解析

```python
# 実行されたコードやコード実行結果を確認
if hasattr(response, 'candidates') and response.candidates:
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'executable') and part.executable:
            code = part.executable.code
            print(f"Generated Code:\n{code}")

        if hasattr(part, 'code_execution_result') and part.code_execution_result:
            output = part.code_execution_result.output
            print(f"Execution Result:\n{output}")
```

### 完全なレスポンス処理

```python
def parse_response(response):
    """レスポンスを構造化して返す"""
    results = {
        'text': response.text,
        'code': [],
        'execution_results': [],
    }

    if hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'executable') and part.executable:
                results['code'].append(part.executable.code)

            if hasattr(part, 'code_execution_result') and part.code_execution_result:
                results['execution_results'].append(
                    part.code_execution_result.output
                )

    return results
```

## エラーハンドリング

### 基本的なエラーハンドリング

```python
from google.genai.errors import ClientError

try:
    response = chat.send_message([image, prompt])
except ClientError as e:
    print(f"API Error: {e}")
except ValueError as e:
    print(f"Configuration Error: {e}")
```

### よくあるエラー

| エラー | 原因 | 対策 |
|--------|------|------|
| `GOOGLE_API_KEY not set` | 環境変数が設定されていない | `export GOOGLE_API_KEY=xxx` |
| `404 NOT_FOUND` | モデル名が間違っている | `gemini-3-flash-preview` を使用 |
| `Invalid argument` | 画像形式がサポートされていない | JPEG/PNG/GIF/WebP を使用 |
| `Resource exhausted` | API レート制限 | 少し待ってから再試行 |

## モデル

| モデル | 説明 |
|--------|------|
| `gemini-3-flash-preview` | Agentic Vision 対応（推奨） |

※ このスキルでは `gemini-3-flash-preview` のみを使用してください。

## API エンドポイント

- **Google AI Studio**: `https://generativelanguage.googleapis.com/`

## 完全な使用例

```python
from google import genai
from google.genai import types
import os

# 初期化
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# チャットセッション作成
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    ),
)

# 画像読み込み
with open("image.png", "rb") as f:
    image_data = f.read()

image = types.Part.from_bytes(data=image_data, mime_type="image/png")

# 分析
response = chat.send_message(
    message=[image, "画像内のオブジェクトを検出してバウンディングボックスを描画して"]
)

# 結果
print(response.text)
```
