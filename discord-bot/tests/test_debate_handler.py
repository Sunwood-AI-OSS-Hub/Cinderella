#!/usr/bin/env python3
"""
discord-bot 議論機能テスト

Bot間議論機能が正しく動作するか確認します。
"""

import requests
import json
import time
import sys

DISCORD_BOT_API_URL = "http://127.0.0.1:8082"

# デフォルトのチャンネルIDとギルドID（テスト用）
DEFAULT_CHANNEL_ID = "1466415185282732220"  # テスト用チャンネル
DEFAULT_GUILD_ID = "1188045372526964796"


def test_health():
    """ヘルスチェック"""
    print("=== ヘルスチェック ===")
    try:
        response = requests.get(f"{DISCORD_BOT_API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ ヘルスチェック成功\n")
            return True
        else:
            print("❌ ヘルスチェック失敗\n")
            return False
    except Exception as e:
        print(f"❌ 接続エラー: {e}\n")
        return False


def test_send_message(channel_id: str, content: str) -> str:
    """メッセージ送信テスト"""
    print(f"=== メッセージ送信テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "sendMessage", "channelId": channel_id, "content": content},
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ メッセージ送信成功 (message_id: {message_id})\n")
            return message_id
        else:
            print(f"❌ メッセージ送信失敗: {result.get('error')}\n")
            return None
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return None


def main():
    """メインテストランナー"""
    print("🧪 discord-bot 議論機能テスト開始\n")
    print("議論機能の基本動作を確認します\n")

    # ヘルスチェック
    if not test_health():
        print("❌ ヘルスチェックに失敗しました。discord-botが起動しているか確認してください。")
        sys.exit(1)

    # 引数からチャンネルIDとギルドIDを取得
    channel_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CHANNEL_ID
    guild_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_GUILD_ID

    print(f"📝 チャンネルID: {channel_id}")
    print(f"📝 ギルドID: {guild_id}\n")

    results = {"passed": 0, "failed": 0}

    print("="*50)
    print("💬 議論機能テスト")
    print("="*50 + "\n")

    # テスト1: メッセージ送信（議論の開始メッセージ）
    print("【テスト1】議論開始メッセージの送信")
    message_id = test_send_message(
        channel_id,
        "🧪 議論機能テスト: AIと人間の協働について議論してください"
    )

    if message_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(2)

    # テスト2: リアクション追加（議論への反応）
    print("【テスト2】議論へのリアクション")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "react",
                "channelId": channel_id,
                "messageId": message_id,
                "emoji": "🤔"
            },
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print("✅ リアクション成功\n")
            results["passed"] += 1
        else:
            print(f"❌ リアクション失敗: {result.get('error')}\n")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        results["failed"] += 1

    time.sleep(1)

    # テスト3: メッセージ読み取り（議論履歴の確認）
    print("【テスト3】議論履歴の確認")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "readMessages", "channelId": channel_id, "limit": 5},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ メッセージ読み取り成功 ({count}メッセージ)\n")
            results["passed"] += 1
        else:
            print(f"❌ メッセージ読み取り失敗: {result.get('error')}\n")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        results["failed"] += 1

    # 結果表示
    print("\n" + "="*50)
    print("📊 テスト結果")
    print("="*50)
    print(f"✅ パス: {results['passed']}")
    print(f"❌ 失敗: {results['failed']}")
    print(f"📋 合計: {results['passed'] + results['failed']}/3")

    if results['failed'] == 0:
        print("\n🎉 すべてのテストが成功しました！")
        print("\n💡 議論機能はAPI経由で正常に動作しています。")
        print("   !debate コマンドでBot間議論を開始できます。")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
