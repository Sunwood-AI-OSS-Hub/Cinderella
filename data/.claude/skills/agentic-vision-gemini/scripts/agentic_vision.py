#!/usr/bin/env python3
"""
Agentic Vision in Gemini 3 Flash - 基本 API スクリプト

Usage:
    export GOOGLE_API_KEY=your_api_key
    python agentic_vision.py <image_path> "<prompt>"
    python agentic_vision.py image.jpg "この画像の詳細を分析して"
    python agentic_vision.py image.png "画像内のオブジェクトを検出してバウンディングボックスを描画して"
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not found.")
    print("Install with: pip install google-genai")
    sys.exit(1)


def load_image(source: str) -> types.Part:
    """画像をファイルパスから読み込む（生バイナリ）"""
    file_path = Path(source)
    if not file_path.exists():
        raise FileNotFoundError(f"Image not found: {source}")

    mime_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }.get(file_path.suffix.lower(), 'image/jpeg')

    # 生バイナリデータを読み込む
    with open(file_path, 'rb') as f:
        data = f.read()

    return types.Part.from_bytes(data=data, mime_type=mime_type)


def analyze_with_agentic_vision(
    image_path: str,
    prompt: str,
    model: str = "gemini-3-flash-preview",
    thinking_level: str = "MEDIUM",
    temperature: float = 0.7,
    verbose: bool = False
) -> dict:
    """
    Agentic Vision で画像を分析

    Args:
        image_path: 画像のパス
        prompt: 分析プロンプト
        model: 使用するモデル名
        thinking_level: 思考レベル (LOW/MEDIUM/HIGH)
        temperature: 生成の創造性パラメータ
        verbose: 詳細出力を有効にするか

    Returns:
        dict: 分析結果（text, code, execution_results）
    """
    # APIキーを環境変数から取得
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. "
            "Get your API key at https://ai.google.dev/"
        )

    client = genai.Client(api_key=api_key)

    # チャットセッションを作成（推奨）
    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            tools=[types.Tool(code_execution=types.ToolCodeExecution)],
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
            temperature=temperature,
        ),
    )

    # 画像を読み込み
    image = load_image(image_path)

    if verbose:
        print(f"Model: {model}")
        print(f"Thinking Level: {thinking_level}")
        print(f"Image: {image_path} ({len(image.data) if hasattr(image, 'data') else 'N/A'} bytes)")
        print(f"Prompt: {prompt}")
        print("-" * 50)

    # API 呼び出し
    response = chat.send_message(message=[image, prompt])

    # 結果を構造化して返す
    results = {
        'text': response.text,
        'code': [],
        'execution_results': [],
    }

    # 実行されたコードを確認
    if hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'executable') and part.executable:
                code = getattr(part.executable, 'code', '')
                results['code'].append(code)
                if verbose:
                    print(f"[CODE]\n{code}")

            if hasattr(part, 'code_execution_result') and part.code_execution_result:
                output = getattr(part.code_execution_result, 'output', '')
                results['execution_results'].append(output)
                if verbose:
                    print(f"[RESULT]\n{output}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Agentic Vision in Gemini 3 Flash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 物体検出
  python agentic_vision.py image.jpg "画像内のオブジェクトを検出してバウンディングボックスを描画して"

  # オブジェクトカウント
  python agentic_vision.py image.png "画像内のオブジェクトを数えて各カテゴリの個数を報告して"

  # 詳細分析
  python agentic_vision.py photo.jpg "この画像の詳細を分析して"
        """
    )
    parser.add_argument('image', help='画像ファイルパス')
    parser.add_argument('prompt', help='分析プロンプト')
    parser.add_argument('--model', default='gemini-3-flash-preview',
                       help='使用するモデル (default: gemini-3-flash-preview)')
    parser.add_argument('--thinking', choices=['LOW', 'MEDIUM', 'HIGH'],
                       default='MEDIUM', help='思考レベル (default: MEDIUM)')
    parser.add_argument('--temperature', type=float, default=0.7,
                       help='生成の創造性 (default: 0.7)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細出力を有効化')
    parser.add_argument('--json', action='store_true',
                       help='結果をJSON形式で出力')

    args = parser.parse_args()

    try:
        results = analyze_with_agentic_vision(
            image_path=args.image,
            prompt=args.prompt,
            model=args.model,
            thinking_level=args.thinking,
            temperature=args.temperature,
            verbose=args.verbose
        )

        if args.json:
            # JSON出力
            output = {
                'text': results['text'],
                'code': results['code'],
                'execution_results': results['execution_results'],
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            # テキスト出力
            print("\n=== Analysis Result ===")
            print(results['text'])

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import logging
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
