#!/usr/bin/env python3
"""
Agentic Vision 用画像ユーティリティ

前処理・後処理のためのヘルパー関数集
"""

import base64
import io
from pathlib import Path
from typing import Tuple, Optional, Union, List

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not found. Some features will be limited.")
    print("Install with: pip install Pillow")


def load_image_as_base64(path: str) -> Tuple[str, str]:
    """
    画像をBase64エンコードして返す

    Args:
        path: 画像ファイルパス

    Returns:
        Tuple[str, str]: (base64_data, mime_type)
    """
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

    return data, mime_type


def save_base64_image(base64_data: str, output_path: str, mime_type: str = 'image/png'):
    """
    Base64画像をファイルに保存

    Args:
        base64_data: Base64エンコードされた画像データ
        output_path: 出力ファイルパス
        mime_type: 画像のMIMEタイプ
    """
    image_bytes = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_bytes)


def resize_image(
    input_path: str,
    output_path: str,
    max_size: Tuple[int, int] = (2048, 2048),
    quality: int = 95
):
    """
    画像をリサイズ（アスペクト比を維持）

    Args:
        input_path: 入力画像パス
        output_path: 出力画像パス
        max_size: 最大サイズ (width, height)
        quality: JPEG品質
    """
    if not HAS_PIL:
        raise ImportError("PIL is required for image resizing")

    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 出力形式を判定
        output_format = Path(output_path).suffix.lower()
        if output_format in ['.jpg', '.jpeg']:
            img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=quality)
        elif output_format == '.png':
            img.save(output_path, 'PNG')
        else:
            img.save(output_path)


def crop_image(
    input_path: str,
    output_path: str,
    box: Tuple[int, int, int, int]
):
    """
    画像をクロップ

    Args:
        input_path: 入力画像パス
        output_path: 出力画像パス
        box: クロップ領域 (left, upper, right, lower)
    """
    if not HAS_PIL:
        raise ImportError("PIL is required for image cropping")

    with Image.open(input_path) as img:
        cropped = img.crop(box)
        cropped.save(output_path)


def draw_bounding_boxes(
    input_path: str,
    output_path: str,
    boxes: List[Union[Tuple[int, int, int, int], Tuple[int, int, int, int, int, int]]],
    labels: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    line_width: int = 3,
    font_size: int = 20,
    normalized: bool = False,
    normalized_max: int = 1000,
    box_format: str = "xyxy"
):
    """
    画像にバウンディングボックスを描画

    Args:
        input_path: 入力画像パス
        output_path: 出力画像パス
        boxes: バウンディングボックスのリスト
            - xyxy形式: [(x1, y1, x2, y2), ...] または [(x1, y1, x2, y2, conf, cls), ...]
            - yxyx形式: [(ymin, xmin, ymax, xmax), ...] (Gemini Agentic Vision)
        labels: ラベルのリスト（オプション）
        colors: 色のリスト（オプション）
        line_width: 線の太さ
        font_size: フォントサイズ
        normalized: 正規化座標かどうか（0-1 または 0-normalized_max）
        normalized_max: 正規化座標の最大値（デフォルト1000 for Gemini）
        box_format: 座標形式 ("xyxy" または "yxyx")

    Example:
        # 通常のピクセル座標
        draw_bounding_boxes(
            'input.jpg', 'output.jpg',
            boxes=[(10, 10, 100, 100), (150, 50, 300, 200)],
            labels=['Object 1', 'Object 2'],
        )

        # Gemini Agentic Vision の正規化座標 (ymin, xmin, ymax, xmax, 0-1000)
        draw_bounding_boxes(
            'input.jpg', 'output.jpg',
            boxes=[(222, 80, 508, 298), (244, 281, 396, 440)],
            labels=['stapler', 'pencil'],
            normalized=True,
            normalized_max=1000,
            box_format="yxyx"
        )
    """
    if not HAS_PIL:
        raise ImportError("PIL is required for drawing bounding boxes")

    with Image.open(input_path) as img:
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # デフォルト色
        default_colors = ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'cyan', 'magenta']

        for i, box in enumerate(boxes):
            # 色を決定
            if colors and i < len(colors):
                color = colors[i]
            else:
                color = default_colors[i % len(default_colors)]

            # 座標を抽出
            if len(box) == 4:
                coords = box
            elif len(box) >= 4:
                coords = box[:4]
            else:
                continue

            # 座標形式に応じて変換
            if box_format == "yxyx":
                # (ymin, xmin, ymax, xmax) -> (xmin, ymin, xmax, ymax)
                ymin, xmin, ymax, xmax = coords
                x1, y1, x2, y2 = xmin, ymin, xmax, ymax
            else:
                # (x1, y1, x2, y2)
                x1, y1, x2, y2 = coords

            # 正規化座標をピクセル座標に変換
            if normalized:
                x1 = int(x1 * width / normalized_max)
                y1 = int(y1 * height / normalized_max)
                x2 = int(x2 * width / normalized_max)
                y2 = int(y2 * height / normalized_max)

            # バウンディングボックスを描画
            draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

            # ラベルを描画（あれば）
            if labels and i < len(labels):
                label = labels[i]

                # ラベル背景
                text_bbox = draw.textbbox((x1, y1 - font_size - 5), label)
                draw.rectangle(text_bbox, fill=color)
                draw.text((x1, y1 - font_size - 5), label, fill='white')

        img.save(output_path)


def annotate_image(
    input_path: str,
    output_path: str,
    annotations: list,
    font_size: int = 16
):
    """
    画像にテキストアノテーションを追加

    Args:
        input_path: 入力画像パス
        output_path: 出力画像パス
        annotations: アノテーションのリスト [{'x': int, 'y': int, 'text': str, 'color': str}, ...]
        font_size: フォントサイズ

    Example:
        annotate_image(
            'input.jpg', 'output.jpg',
            annotations=[
                {'x': 100, 'y': 50, 'text': 'Label A', 'color': 'red'},
                {'x': 200, 'y': 150, 'text': 'Label B', 'color': 'blue'}
            ]
        )
    """
    if not HAS_PIL:
        raise ImportError("PIL is required for image annotation")

    with Image.open(input_path) as img:
        draw = ImageDraw.Draw(img)

        for ann in annotations:
            x = ann.get('x', 0)
            y = ann.get('y', 0)
            text = ann.get('text', '')
            color = ann.get('color', 'red')

            # 背景付きテキスト
            text_bbox = draw.textbbox((x, y), text)
            padding = 3
            bg_box = (
                text_bbox[0] - padding,
                text_bbox[1] - padding,
                text_bbox[2] + padding,
                text_bbox[3] + padding
            )
            draw.rectangle(bg_box, fill='white', outline=color)
            draw.text((x, y), text, fill=color)

        img.save(output_path)


def get_image_info(path: str) -> dict:
    """
    画像のメタ情報を取得

    Args:
        path: 画像ファイルパス

    Returns:
        dict: 画像情報
    """
    if not HAS_PIL:
        # PILなしでも基本情報は取得
        file_path = Path(path)
        return {
            'path': str(path),
            'size_bytes': file_path.stat().st_size,
            'extension': file_path.suffix.lower()
        }

    with Image.open(path) as img:
        return {
            'path': str(path),
            'width': img.width,
            'height': img.height,
            'mode': img.mode,
            'format': img.format,
            'size_bytes': Path(path).stat().st_size
        }


def optimize_for_api(
    input_path: str,
    output_path: str,
    max_size: Tuple[int, int] = (4096, 4096),
    max_bytes: int = 20 * 1024 * 1024,  # 20MB
    quality: int = 85
):
    """
    API送信用に画像を最適化

    Args:
        input_path: 入力画像パス
        output_path: 出力画像パス
        max_size: 最大サイズ
        max_bytes: 最大ファイルサイズ（バイト）
        quality: JPEG品質（段階的に下げる）
    """
    if not HAS_PIL:
        raise ImportError("PIL is required for image optimization")

    with Image.open(input_path) as img:
        # サイズを制限
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # RGB変換（JPEG用）
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # ファイルサイズを確認しながら品質を調整
        current_quality = quality
        while current_quality > 20:
            buffer = io.BytesIO()
            img.save(buffer, 'JPEG', quality=current_quality)

            if buffer.tell() <= max_bytes:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return

            current_quality -= 10

        # 最低品質でも保存
        img.save(output_path, 'JPEG', quality=20)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_utils.py <image_path>")
        print("       Shows image information")
        sys.exit(1)

    info = get_image_info(sys.argv[1])
    for key, value in info.items():
        print(f"{key}: {value}")
