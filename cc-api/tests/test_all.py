#!/usr/bin/env python3
"""
discord-bot API フル機能テストランナー

すべてのテストスイート（メッセージ、チャンネル、ギルド）を実行し、
統合された結果を表示します。
"""

import subprocess
import sys


def run_test_suite(test_file: str, name: str) -> dict:
    """テストスイートを実行して結果を返す"""
    print(f"\n{'='*60}")
    print(f"🚀 {name} を実行中...")
    print('='*60 + '\n')

    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=False,
        text=True
    )

    return {
        "name": name,
        "exit_code": result.returncode,
        "success": result.returncode == 0
    }


def main():
    """メインテストランナー"""
    print("🧪 discord-bot API フル機能テスト開始\n")
    print("36個すべてのアクションをテストします\n")

    # 引数からチャンネルID、ギルドID、ユーザーIDを取得
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # テストスイートの定義
    test_suites = [
        {
            "file": "test_message_handlers.py",
            "name": "Message Handlers (15 tests)",
            "module": "test_message_handlers"
        },
        {
            "file": "test_channel_handlers.py",
            "name": "Channel Handlers (10 tests)",
            "module": "test_channel_handlers"
        },
        {
            "file": "test_guild_handlers.py",
            "name": "Guild Handlers (11 tests)",
            "module": "test_guild_handlers"
        },
    ]

    results = []
    all_passed = True

    for suite in test_suites:
        # 引数を渡してテストを実行
        cmd = [sys.executable, suite["file"]] + args
        print(f"\n{'='*60}")
        print(f"🚀 {suite['name']} を実行中...")
        print('='*60 + '\n')

        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True
        )

        results.append({
            "name": suite["name"],
            "exit_code": result.returncode,
            "success": result.returncode == 0
        })

        if result.returncode != 0:
            all_passed = False

    # 統合結果の表示
    print("\n" + "="*60)
    print("📊 統合テスト結果")
    print("="*60)

    for result in results:
        status = "✅ パス" if result["success"] else "❌ 失敗"
        print(f"{status}: {result['name']}")

    print("\n" + "="*60)
    print("📋 合計: 36 tests")
    print("="*60)

    if all_passed:
        print("\n🎉 すべてのテストスイートが成功しました！")
        sys.exit(0)
    else:
        failed_count = sum(1 for r in results if not r["success"])
        print(f"\n⚠️ {failed_count}個のテストスイートが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
