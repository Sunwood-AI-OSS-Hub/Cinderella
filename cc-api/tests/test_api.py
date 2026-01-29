#!/usr/bin/env python3
"""
Cinderella API テストスクリプト

FastAPI サーバーが正常に動作しているか確認します。
テスト結果を tests/README.md にレポートとして出力します。
"""

import requests
import json
import subprocess
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
            exit_code = data.get('exit_code', -1)
            stdout_json = data.get('stdout_json', {})
            result = stdout_json.get('result', 'N/A')[:200]

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
            exit_code = data.get('exit_code', -1)
            stdout_json = data.get('stdout_json', {})
            result = stdout_json.get('result', 'N/A')[:200]

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


def test_dice_roll(reporter: TestReporter):
    """サイコロを振るテスト"""
    print("=== サイコロアプリテスト ===")
    details = ""
    status = "PASS"

    try:
        response = requests.post(
            "http://127.0.0.1:8081/v1/claude/run",
            json={
                "prompt": "workspace にフォルダを作って、そこにシンプルなHTMLのサイコロアプリを作って。結果のファイルパスだけ答えて。",
                "cwd": "/workspace",
                "allowed_tools": ["Write", "Bash", "Read"],
                "timeout_sec": 30,
            },
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            exit_code = data.get('exit_code', -1)
            stdout_json = data.get('stdout_json', {})
            result = stdout_json.get('result', 'N/A')

            print(f"Exit Code: {exit_code}")
            print(f"Dice App Result: {result}")

            # 結果にHTMLファイルパスが含まれているかチェック
            import re
            html_match = re.search(r'/workspace/.+\.html', str(result))
            file_path = html_match.group() if html_match else None

            details += f"- **Status Code**: {response.status_code}\n"
            details += f"- **Exit Code**: {exit_code}\n"
            details += f"- **Result**: `{result}`\n"

            if file_path and ".html" in file_path:
                details += f"- **HTML App Created**: {file_path} 🎲\n"
                print(f"✅ HTMLアプリ作成: {file_path} 🎲\n")
            else:
                status = "FAIL"
                details += f"- **Error**: HTMLファイルが見つかりません\n"
                print(f"❌ HTMLファイルが見つかりません\n")
        else:
            status = "FAIL"
            details += f"- **Status Code**: {response.status_code}\n"
            details += f"- **Error**: {response.json()}\n"
            print(f"❌ サイコロテスト失敗: {response.json()}\n")
    except Exception as e:
        status = "FAIL"
        details += f"- **エラー**: {e}\n"
        print(f"❌ サイコロテスト失敗: {e}\n")

    reporter.add_result("サイコロアプリテスト", status, details)


def test_cinderella_user_config(reporter: TestReporter):
    """cinderella ユーザー設定を確認"""
    print("=== cinderella ユーザー設定テスト ===")
    details = ""
    status = "PASS"

    try:
        # コンテナ名を取得（docker-composeで起動している想定）
        container_name = "cinderella-cc-api-1"

        # 実行ユーザーを確認
        result = subprocess.run(
            ["docker", "exec", container_name, "whoami"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        whoami = result.stdout.strip()
        print(f"実行ユーザー: {whoami}")

        if whoami != "cinderella":
            status = "FAIL"
            details += f"- **実行ユーザー**: {whoami}（期待: cinderella）\n"
            print(f"❌ 実行ユーザーが cinderella ではありません: {whoami}\n")
            reporter.add_result("cinderella ユーザー設定", status, details)
            return

        details += f"- **実行ユーザー**: {whoami} ✔️\n"

        # ユーザー詳細情報を確認
        result = subprocess.run(
            ["docker", "exec", container_name, "id"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        id_info = result.stdout.strip()
        print(f"ユーザー情報: {id_info}")

        # sudo グループに所属しているか確認
        if "sudo" not in id_info:
            status = "FAIL"
            details += f"- **エラー**: sudo グループに所属していません\n"
            details += f"- **ユーザー情報**: `{id_info}`\n"
            print("❌ sudo グループに所属していません\n")
        else:
            details += f"- **sudo グループ**: 所属済み ✔️\n"

        # パスワードなし sudo を確認
        result = subprocess.run(
            ["docker", "exec", container_name, "sudo", "whoami"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        sudo_result = result.stdout.strip()
        print(f"sudo whoami: {sudo_result}")

        if sudo_result != "root":
            status = "FAIL"
            details += f"- **パスワードなし sudo**: 失敗（結果: {sudo_result}）\n"
            print("❌ パスワードなし sudo が失敗しました\n")
        else:
            details += f"- **パスワードなし sudo**: 動作確認 ✔️\n"

        # claude コマンドのパスを確認
        result = subprocess.run(
            ["docker", "exec", container_name, "which", "claude"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        claude_path = result.stdout.strip()
        print(f"claude コマンド: {claude_path}")

        if result.returncode != 0:
            status = "FAIL"
            details += f"- **claude コマンド**: 見つかりません\n"
            print("❌ claude コマンドが見つかりません\n")
        else:
            details += f"- **claude コマンド**: {claude_path} ✔️\n"

        # Python パッケージを確認
        result = subprocess.run(
            ["docker", "exec", container_name, "python", "-c",
             "import fastapi, uvicorn, pydantic; print('OK')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        pkg_check = result.stdout.strip()
        print(f"Python パッケージ: {pkg_check}")

        if pkg_check != "OK":
            status = "FAIL"
            details += f"- **Python パッケージ**: インポートエラー\n"
            print("❌ Python パッケージのインポートに失敗しました\n")
        else:
            details += f"- **Python パッケージ**: fastapi, uvicorn, pydantic OK ✔️\n"

        if status == "PASS":
            print("✅ cinderella ユーザー設定テスト成功\n")
        else:
            print("⚠️ cinderella ユーザー設定テスト完了（一部失敗）\n")

    except subprocess.TimeoutExpired:
        status = "FAIL"
        details += f"- **エラー**: コマンド実行がタイムアウトしました\n"
        print("❌ コマンド実行がタイムアウトしました\n")
    except FileNotFoundError:
        status = "FAIL"
        details += f"- **エラー**: docker コマンドが見つかりません\n"
        details += f"- **確認**: Docker がインストールされているか確認してください\n"
        print("❌ docker コマンドが見つかりません\n")
    except Exception as e:
        status = "FAIL"
        details += f"- **エラー**: {e}\n"
        print(f"❌ cinderella ユーザー設定テスト失敗: {e}\n")

    reporter.add_result("cinderella ユーザー設定", status, details)


if __name__ == "__main__":
    print("🧪 Cinderella API テスト開始\n")

    reporter = TestReporter()

    try:
        test_health(reporter)
        test_cinderella_user_config(reporter)
        test_simple_prompt(reporter)
        test_with_bash_tool(reporter)
        test_dice_roll(reporter)

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
