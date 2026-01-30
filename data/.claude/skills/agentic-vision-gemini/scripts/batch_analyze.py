#!/usr/bin/env python3
"""
Agentic Vision バッチ分析スクリプト

複数の画像を一括で分析し、結果をJSON/CSVで出力

Usage:
    export GOOGLE_API_KEY=your_api_key
    python batch_analyze.py --input-dir ./images --prompt "画像を説明して"
    python batch_analyze.py --input-list images.txt --prompt "オブジェクトを数えて"
    python batch_analyze.py --input-dir ./images --prompt-file prompt.txt --output results.json
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not found.")
    print("Install with: pip install google-genai")
    sys.exit(1)


def load_image_bytes(image_path: str) -> bytes:
    """画像をバイト列として読み込む"""
    with open(image_path, 'rb') as f:
        return f.read()


def get_mime_type(file_path: str) -> str:
    """ファイルパスからMIMEタイプを取得"""
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    return mime_types.get(Path(file_path).suffix.lower(), 'image/jpeg')


def get_image_files(input_dir: str, extensions: List[str] = None) -> List[Path]:
    """
    ディレクトリから画像ファイルを取得

    Args:
        input_dir: 入力ディレクトリパス
        extensions: 対象拡張子のリスト

    Returns:
        List[Path]: 画像ファイルパスのリスト
    """
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    image_files = []
    for ext in extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))

    return sorted(image_files)


def load_image_list(list_file: str) -> List[str]:
    """
    ファイルから画像パスリストを読み込み

    Args:
        list_file: 画像リストファイルパス

    Returns:
        List[str]: 画像パスのリスト
    """
    with open(list_file, 'r') as f:
        lines = f.readlines()

    return [line.strip() for line in lines if line.strip() and not line.startswith('#')]


def analyze_single_image(
    image_path: str,
    prompt: str,
    model: str,
    thinking_level: str,
    temperature: float,
    api_key: str,
    retry_count: int = 3,
    retry_delay: float = 1.0
) -> dict:
    """
    単一画像を分析（リトライ付き）

    Args:
        image_path: 画像パス
        prompt: 分析プロンプト
        model: モデル名
        thinking_level: 思考レベル
        temperature: 温度パラメータ
        api_key: Google APIキー
        retry_count: リトライ回数
        retry_delay: リトライ間隔（秒）

    Returns:
        dict: 分析結果
    """
    for attempt in range(retry_count):
        try:
            client = genai.Client(api_key=api_key)

            # チャットセッションを作成
            chat = client.chats.create(
                model=model,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
                    thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
                    temperature=temperature,
                ),
            )

            # 画像を読み込み
            image_data = load_image_bytes(image_path)
            mime_type = get_mime_type(image_path)
            image = types.Part.from_bytes(data=image_data, mime_type=mime_type)

            # 分析実行
            response = chat.send_message(message=[image, prompt])

            return {
                'source': image_path,
                'status': 'success',
                'text': response.text,
                'error': None
            }

        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                return {
                    'source': image_path,
                    'status': 'error',
                    'text': '',
                    'error': str(e)
                }

    return {
        'source': image_path,
        'status': 'error',
        'text': '',
        'error': 'Unknown error'
    }


def batch_analyze(
    image_sources: List[str],
    prompt: str,
    model: str = "gemini-3-flash-preview",
    thinking_level: str = "MEDIUM",
    temperature: float = 0.7,
    max_workers: int = 3,
    rate_limit_delay: float = 0.5,
    progress_callback = None
) -> List[dict]:
    """
    複数画像を並列で分析

    Args:
        image_sources: 画像パスのリスト
        prompt: 分析プロンプト
        model: モデル名
        thinking_level: 思考レベル
        temperature: 温度パラメータ
        max_workers: 並列ワーカー数
        rate_limit_delay: レート制限用の遅延（秒）
        progress_callback: 進捗コールバック関数

    Returns:
        List[dict]: 分析結果のリスト
    """
    # APIキーを取得
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. "
            "Get your API key at https://ai.google.dev/"
        )

    results = []
    total = len(image_sources)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for i, source in enumerate(image_sources):
            # レート制限対策
            if i > 0:
                time.sleep(rate_limit_delay)

            future = executor.submit(
                analyze_single_image,
                source, prompt, model, thinking_level, temperature, api_key
            )
            futures[future] = source

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total, result)

    # 元の順序でソート
    source_to_result = {r['source']: r for r in results}
    return [source_to_result[s] for s in image_sources]


def save_results_json(results: List[dict], output_path: str):
    """結果をJSONで保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def save_results_csv(results: List[dict], output_path: str):
    """結果をCSVで保存"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['source', 'status', 'text', 'error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_progress(current: int, total: int, result: dict):
    """進捗表示"""
    status = "✓" if result['status'] == 'success' else "✗"
    source = Path(result['source']).name
    print(f"[{current}/{total}] {status} {source}")


def main():
    parser = argparse.ArgumentParser(
        description='Agentic Vision バッチ分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # ディレクトリ内の全画像を分析
  python batch_analyze.py -d ./images -p "画像を説明して"

  # 画像リストファイルから読み込み
  python batch_analyze.py -l images.txt -p "オブジェクトを検出して"

  # 結果をJSONで保存
  python batch_analyze.py -d ./images -p "物体を数えて" -o results.json

  # 思考レベルをHIGHに設定
  python batch_analyze.py -d ./images -p "詳細分析" --thinking HIGH
        """
    )

    # 入力オプション（相互排他）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input-dir', '-d',
                            help='画像ディレクトリパス')
    input_group.add_argument('--input-list', '-l',
                            help='画像リストファイルパス（1行1画像）')

    # プロンプトオプション
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument('--prompt', '-p',
                             help='分析プロンプト')
    prompt_group.add_argument('--prompt-file', '-pf',
                             help='プロンプトファイルパス')

    # その他オプション
    parser.add_argument('--output', '-o',
                       help='出力ファイルパス（.json または .csv）')
    parser.add_argument('--model', default='gemini-3-flash-preview',
                       help='モデル名 (default: gemini-3-flash-preview)')
    parser.add_argument('--thinking', choices=['LOW', 'MEDIUM', 'HIGH'],
                       default='MEDIUM', help='思考レベル (default: MEDIUM)')
    parser.add_argument('--temperature', type=float, default=0.7,
                       help='温度パラメータ (default: 0.7)')
    parser.add_argument('--workers', type=int, default=3,
                       help='並列ワーカー数 (default: 3)')
    parser.add_argument('--rate-limit', type=float, default=0.5,
                       help='リクエスト間隔（秒） (default: 0.5)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='進捗表示を抑制')

    args = parser.parse_args()

    # 画像リストを取得
    if args.input_dir:
        image_sources = [str(p) for p in get_image_files(args.input_dir)]
    else:
        image_sources = load_image_list(args.input_list)

    if not image_sources:
        print("No images found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(image_sources)} images")

    # プロンプトを取得
    if args.prompt:
        prompt = args.prompt
    else:
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()

    # バッチ分析を実行
    progress_cb = None if args.quiet else print_progress

    try:
        results = batch_analyze(
            image_sources=image_sources,
            prompt=prompt,
            model=args.model,
            thinking_level=args.thinking,
            temperature=args.temperature,
            max_workers=args.workers,
            rate_limit_delay=args.rate_limit,
            progress_callback=progress_cb
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 結果を保存
    if args.output:
        if args.output.endswith('.csv'):
            save_results_csv(results, args.output)
        else:
            save_results_json(results, args.output)
        print(f"\nResults saved to: {args.output}")
    else:
        # 標準出力にJSON
        print(json.dumps(results, ensure_ascii=False, indent=2))

    # サマリー表示
    success = sum(1 for r in results if r['status'] == 'success')
    errors = len(results) - success
    print(f"\nSummary: {success} success, {errors} errors")


if __name__ == '__main__':
    main()
