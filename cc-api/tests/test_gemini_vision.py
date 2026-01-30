#!/usr/bin/env python3
"""
agentic-vision-gemini スキル テストスクリプト

Gemini 3 Flash の Agentic Vision を使った画像分析をテストします。
"""

import requests
import json
import subprocess
from pathlib import Path


API_URL = "http://127.0.0.1:8081/v1/claude/run"
SAMPLE_IMAGE = "/workspace/tests/sample.png"


def test_gemini_vision_object_detection():
    """物体検出テスト"""
    print("=== Agentic Vision 物体検出テスト ===")

    prompt = f"""agentic-vision-gemini スキルを使って、画像 {SAMPLE_IMAGE} を分析して。

画像内のオブジェクトを検出して、バウンディングボックスを描画して。
検出したオブジェクトの数と種類を報告して。
"""

    response = requests.post(
        API_URL,
        json={
            "prompt": prompt,
            "cwd": "/workspace",
            "skip_permissions": True,
            "timeout_sec": 120,
        },
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        exit_code = data.get('exit_code', -1)
        stdout_json = data.get('stdout_json', {})
        result = stdout_json.get('result', '')

        print(f"Exit Code: {exit_code}")
        print(f"Result:\n{result}")
        print("✅ テスト成功\n")
        return True
    else:
        print(f"❌ テスト失敗: {response.json()}\n")
        return False


def test_gemini_vision_detail_zoom():
    """ズーム詳細検査テスト"""
    print("=== Agentic Vision ズーム詳細検査テスト ===")

    prompt = f"""agentic-vision-gemini スキルを使って、画像 {SAMPLE_IMAGE} を分析して。

画像内の細かいディテールを拡大して読み取って。
見えるテキストやラベルがあれば、全て抽出して。
"""

    response = requests.post(
        API_URL,
        json={
            "prompt": prompt,
            "cwd": "/workspace",
            "skip_permissions": True,
            "timeout_sec": 120,
        },
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        exit_code = data.get('exit_code', -1)
        stdout_json = data.get('stdout_json', {})
        result = stdout_json.get('result', '')

        print(f"Exit Code: {exit_code}")
        print(f"Result:\n{result}")
        print("✅ テスト成功\n")
        return True
    else:
        print(f"❌ テスト失敗: {response.json()}\n")
        return False


def test_container_google_api_key():
    """コンテナ内で GOOGLE_API_KEY 環境変数を確認"""
    print("=== GOOGLE_API_KEY 環境変数確認 ===")

    try:
        result = subprocess.run(
            ["docker", "exec", "cinderella-cc-api-1", "sh", "-c",
             "echo $GOOGLE_API_KEY | cut -c1-10"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        key_preview = result.stdout.strip()
        print(f"GOOGLE_API_KEY (先頭10文字): {key_preview}")

        if key_preview and len(key_preview) > 5:
            print("✅ GOOGLE_API_KEY が設定されています\n")
            return True
        else:
            print("❌ GOOGLE_API_KEY が設定されていません\n")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False


def test_container_google_genai_package():
    """コンテナ内で google-genai パッケージを確認"""
    print("=== google-genai パッケージ確認 ===")

    try:
        result = subprocess.run(
            ["docker", "exec", "cinderella-cc-api-1", "python", "-c",
             "from google import genai; print('google-genai installed')"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = result.stdout.strip()
        print(f"Package check: {output}")

        if result.returncode == 0 and "installed" in output:
            print("✅ google-genai パッケージがインストールされています\n")
            return True
        else:
            print(f"❌ パッケージ確認失敗: {result.stderr}\n")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False


if __name__ == "__main__":
    print("🧪 Agentic Vision Gemini テスト開始\n")
    print("=" * 60)

    results = []

    # 1. 環境変数確認
    results.append(("GOOGLE_API_KEY 確認", test_container_google_api_key()))

    # 2. パッケージ確認
    results.append(("google-genai パッケージ確認", test_container_google_genai_package()))

    # 3. 物体検出テスト
    results.append(("物体検出", test_gemini_vision_object_detection()))

    # 4. ズーム詳細検査テスト
    results.append(("ズーム詳細検査", test_gemini_vision_detail_zoom()))

    print("=" * 60)
    print("\n📊 テスト結果サマリー:")

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n合計: {passed}/{total} テスト成功")

    if passed == total:
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print(f"\n⚠️ {total - passed} 個のテストが失敗しました")
