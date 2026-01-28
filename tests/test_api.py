#!/usr/bin/env python3
"""
Cinderella API テストスクリプト

FastAPI サーバーが正常に動作しているか確認します。
テスト結果を tests/README.md にレポートとして出力します。
"""

import requests
import json
from datetime import datetime
from pathlib import Path


class TestReporter:
    """テスト結果を記録してレポートを出力する"""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_result(self, name: str, status: str, details: str = ""):
        self.results.append({
            "name": name,
            "status": status,  # "PASS", "FAIL", "SKIP"
            "details": details
        })

    def generate_report(self) -> str:
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)

        report = f"""# Cinderella API テストレポート

**生成日時**: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}

## サマリー

| 結果 | 数 |
|------|-----|
| ✅ PASS | {passed} |
| ❌ FAIL | {failed} |
| 📊 合計 | {total} |

{"## 🎉 すべてのテストが成功しました！" if failed == 0 else "## ⚠️ 一部のテストが失敗しました"}

---

## テスト詳細

"""

        for i, result in enumerate(self.results, 1):
            icon = "✅" if result["status"] == "PASS" else "❌"
            report += f"""### {i}. {result["name"]}

**結果**: {icon} {result["status"]}

{result["details"]}

---

"""

        report += """## 実行方法

```bash
# サーバーを起動
docker compose up -d

# テストを実行
python3 tests/test_api.py
```

## テスト環境

| 項目 | 値 |
|------|-----|
| サーバー | http://127.0.0.1:8081 |
| テストファイル | tests/test_api.py |
"""
        return report

    def save_report(self, path: str = "tests/README.md"):
        report = self.generate_report()
        Path(path).write_text(report, encoding="utf-8")
        print(f"\n📄 レポートを {path} に保存しました")


def test_health(reporter: TestReporter):
    """ヘルスチェック"""
    print("=== ヘルスチェック ===")
    details = ""
    status = "PASS"

    try:
        response = requests.get("http://127.0.0.1:8081/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        details += f"- **Status Code**: {response.status_code}\n"
        details += f"- **Response**: `{response.json()}`\n"
        print("✅ ヘルスチェック成功\n")
    except Exception as e:
        status = "FAIL"
        details += f"- **エラー**: {e}\n"
        print(f"❌ ヘルスチェック失敗: {e}\n")

    reporter.add_result("ヘルスチェック", status, details)


def test_simple_prompt(reporter: TestReporter):
    """簡単なプロンプトを送信"""
    print("=== 簡単なプロンプトテスト ===")
    details = ""
    status = "PASS"

    try:
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
            exit_code = data['exit_code']
            result = data['stdout_json'].get('result', 'N/A')[:200]

            print(f"Exit Code: {exit_code}")
            print(f"Result: {result}...")

            details += f"- **Status Code**: {response.status_code}\n"
            details += f"- **Exit Code**: {exit_code}\n"
            details += f"- **Response Preview**: `{result}...`\n"
            print("✅ プロンプトテスト成功\n")
        else:
            status = "FAIL"
            details += f"- **Status Code**: {response.status_code}\n"
            details += f"- **Error**: {response.json()}\n"
            print(f"❌ プロンプトテスト失敗: {response.json()}\n")
    except Exception as e:
        status = "FAIL"
        details += f"- **エラー**: {e}\n"
        print(f"❌ プロンプトテスト失敗: {e}\n")

    reporter.add_result("簡単なプロンプトテスト", status, details)


def test_with_bash_tool(reporter: TestReporter):
    """Bashツールを許可して実行"""
    print("=== Bashツールテスト ===")
    details = ""
    status = "PASS"

    try:
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
            exit_code = data['exit_code']
            result = data['stdout_json'].get('result', 'N/A')[:200]

            print(f"Exit Code: {exit_code}")
            print(f"Result: {result}...")

            details += f"- **Status Code**: {response.status_code}\n"
            details += f"- **Exit Code**: {exit_code}\n"
            details += f"- **Response Preview**: `{result}...`\n"
            print("✅ Bashツールテスト成功\n")
        else:
            status = "FAIL"
            details += f"- **Status Code**: {response.status_code}\n"
            details += f"- **Error**: {response.json()}\n"
            print(f"❌ Bashツールテスト失敗: {response.json()}\n")
    except Exception as e:
        status = "FAIL"
        details += f"- **エラー**: {e}\n"
        print(f"❌ Bashツールテスト失敗: {e}\n")

    reporter.add_result("Bashツールテスト", status, details)


if __name__ == "__main__":
    print("🧪 Cinderella API テスト開始\n")

    reporter = TestReporter()

    try:
        test_health(reporter)
        test_simple_prompt(reporter)
        test_with_bash_tool(reporter)

        failed = sum(1 for r in reporter.results if r["status"] == "FAIL")
        if failed == 0:
            print("🎉 すべてのテストが完了しました！")
        else:
            print(f"⚠️ {failed} 個のテストが失敗しました")

        reporter.save_report()

    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        print("   'docker compose up -d' でサーバーを起動してください")
    except Exception as e:
        print(f"❌ エラー: {e}")
