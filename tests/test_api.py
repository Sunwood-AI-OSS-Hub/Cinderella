#!/usr/bin/env python3
"""
Cinderella API テストスクリプト

FastAPI サーバーが正常に動作しているか確認します。
"""

import requests
import json


def test_health():
    """ヘルスチェック"""
    print("=== ヘルスチェック ===")
    response = requests.get("http://127.0.0.1:8081/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    print("✅ ヘルスチェック成功\n")


def test_simple_prompt():
    """簡単なプロンプトを送信"""
    print("=== 簡単なプロンプトテスト ===")
    response = requests.post(
        "http://127.0.0.1:8081/v1/claude/run",
        json={
            "prompt": "こんにちは、自己紹介して",
            "cwd": "/workspace",
            "allowed_tools": ["Read"],
            "timeout_sec": 30,
        },
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Exit Code: {data['exit_code']}")
        print(f"Result: {data['stdout_json'].get('result', 'N/A')[:200]}...")
        print("✅ プロンプトテスト成功\n")
    else:
        print(f"Error: {response.json()}")
        print("❌ プロンプトテスト失敗\n")


def test_with_bash_tool():
    """Bashツールを許可して実行"""
    print("=== Bashツールテスト ===")
    response = requests.post(
        "http://127.0.0.1:8081/v1/claude/run",
        json={
            "prompt": "現在の日時を表示して",
            "cwd": "/workspace",
            "allowed_tools": ["Read", "Bash"],
            "timeout_sec": 30,
        },
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Exit Code: {data['exit_code']}")
        print(f"Result: {data['stdout_json'].get('result', 'N/A')[:200]}...")
        print("✅ Bashツールテスト成功\n")
    else:
        print(f"Error: {response.json()}")
        print("❌ Bashツールテスト失敗\n")


if __name__ == "__main__":
    print("🧪 Cinderella API テスト開始\n")

    try:
        test_health()
        test_simple_prompt()
        test_with_bash_tool()
        print("🎉 すべてのテストが完了しました！")
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        print("   'docker compose up -d' でサーバーを起動してください")
    except AssertionError as e:
        print(f"❌ アサーションエラー: {e}")
    except Exception as e:
        print(f"❌ エラー: {e}")
