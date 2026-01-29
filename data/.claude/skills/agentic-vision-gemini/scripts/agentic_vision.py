#!/usr/bin/env python3
"""
Agentic Vision in Gemini 3 Flash - 基本 API スクリプト

Usage:
    python agentic_vision.py <image_path_or_url> "<prompt>"
    python agentic_vision.py image.jpg "この画像の詳細を分析して"
    python agentic_vision.py https://example.com/img.png "Count objects"
"""

import argparse
import base64
import json
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
    """画像をファイルパスまたはURLから読み込む"""
    if source.startswith(('http://', 'https://')):
        # URL から読み込み
        mime_type = 'image/jpeg'
        if source.lower().endswith('.png'):
            mime_type = 'image/png'
        elif source.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif source.lower().endswith('.webp'):
            mime_type = 'image/webp'
        
        return types.Part.from_uri(file_uri=source, mime_type=mime_type)
    else:
        # ローカルファイルから読み込み
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
        
        with open(file_path, 'rb') as f:
            data = base64.standard_b64encode(f.read()).decode('utf-8')
        
        return types.Part.from_bytes(data=data, mime_type=mime_type)


def analyze_with_agentic_vision(
    image_source: str,
    prompt: str,
    model: str = "gemini-3-flash-preview",
    temperature: float = 0.7,
    verbose: bool = False
) -> dict:
    """
    Agentic Vision で画像を分析
    
    Args:
        image_source: 画像のパスまたはURL
        prompt: 分析プロンプト
        model: 使用するモデル名
        temperature: 生成の創造性パラメータ
        verbose: 詳細出力を有効にするか
    
    Returns:
        dict: 分析結果（text, code, execution_results, images）
    """
    client = genai.Client()
    
    # 画像を読み込み
    image = load_image(image_source)
    
    # Code Execution を有効化した設定
    config = types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        temperature=temperature,
    )
    
    # API 呼び出し
    response = client.models.generate_content(
        model=model,
        contents=[image, prompt],
        config=config,
    )
    
    # 結果を構造化して返す
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
                if verbose:
                    print(f"[TEXT] {part.text}")
            
            if hasattr(part, 'executable_code'):
                code = part.executable_code.code
                results['code'].append(code)
                if verbose:
                    print(f"[CODE]\n{code}")
            
            if hasattr(part, 'code_execution_result'):
                output = part.code_execution_result.output
                results['execution_results'].append(output)
                if verbose:
                    print(f"[RESULT] {output}")
            
            if hasattr(part, 'inline_data'):
                results['images'].append({
                    'mime_type': part.inline_data.mime_type,
                    'data': part.inline_data.data
                })
                if verbose:
                    print(f"[IMAGE] Generated image ({part.inline_data.mime_type})")
    
    return results


def save_generated_images(results: dict, output_dir: str = ".") -> list:
    """生成された画像を保存"""
    saved_paths = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for i, img_data in enumerate(results.get('images', [])):
        ext = img_data['mime_type'].split('/')[-1]
        filename = output_path / f"generated_{i+1}.{ext}"
        
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(img_data['data']))
        
        saved_paths.append(str(filename))
        print(f"Saved: {filename}")
    
    return saved_paths


def main():
    parser = argparse.ArgumentParser(
        description='Agentic Vision in Gemini 3 Flash',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('image', help='画像ファイルパスまたはURL')
    parser.add_argument('prompt', help='分析プロンプト')
    parser.add_argument('--model', default='gemini-3-flash-preview',
                       help='使用するモデル (default: gemini-3-flash-preview)')
    parser.add_argument('--temperature', type=float, default=0.7,
                       help='生成の創造性 (default: 0.7)')
    parser.add_argument('--output-dir', default='.',
                       help='生成画像の保存先 (default: current directory)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細出力を有効化')
    parser.add_argument('--json', action='store_true',
                       help='結果をJSON形式で出力')
    
    args = parser.parse_args()
    
    try:
        results = analyze_with_agentic_vision(
            image_source=args.image,
            prompt=args.prompt,
            model=args.model,
            temperature=args.temperature,
            verbose=args.verbose
        )
        
        if args.json:
            # JSON出力（画像データは除外）
            output = {
                'text': results['text'],
                'code': results['code'],
                'execution_results': results['execution_results'],
                'image_count': len(results['images'])
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            # テキスト出力
            print("\n=== Analysis Result ===")
            print('\n'.join(results['text']))
        
        # 生成された画像を保存
        if results['images']:
            save_generated_images(results, args.output_dir)
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
