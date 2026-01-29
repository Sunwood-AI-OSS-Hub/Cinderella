#!/usr/bin/env python3
"""
discord-bot API テストスクリプト（フル機能）

Discord操作APIが正しく動作するか確認します。
"""

import requests
import json
import time
import sys

DISCORD_BOT_API_URL = "http://127.0.0.1:8082"

# デフォルトのチャンネルIDとギルドID（テスト用）
DEFAULT_CHANNEL_ID = "1465315494595792936"
DEFAULT_GUILD_ID = "1188045372526964796"
DEFAULT_USER_ID = "539207222494699520"  # サブエージェントのユーザーID


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


def test_send_message(channel_id: str, content: str):
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


def test_react(channel_id: str, message_id: str, emoji: str):
    """リアクションテスト"""
    print(f"=== リアクションテスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "react", "channelId": channel_id, "messageId": message_id, "emoji": emoji},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ リアクション成功\n")
            return True
        else:
            print(f"❌ リアクション失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_reactions_list(channel_id: str, message_id: str):
    """リアクション一覧テスト"""
    print(f"=== リアクション一覧テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "reactions", "channelId": channel_id, "messageId": message_id, "limit": 10},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = len(result.get("data", {}).get("reactions", []))
            print(f"✅ リアクション一覧取得成功 ({count}リアクション)\n")
            return True
        else:
            print(f"❌ リアクション一覧取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_read_messages(channel_id: str, limit: int = 5):
    """メッセージ読み取りテスト"""
    print(f"=== メッセージ読み取りテスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "readMessages", "channelId": channel_id, "limit": limit},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ メッセージ読み取り成功 ({count}メッセージ)\n")
            return True
        else:
            print(f"❌ メッセージ読み取り失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_fetch_message(guild_id: str, channel_id: str, message_id: str):
    """メッセージ取得テスト"""
    print(f"=== メッセージ取得テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "fetchMessage", "guildId": guild_id, "channelId": channel_id, "messageId": message_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            content = result.get("data", {}).get("content", "")[:50]
            print(f"✅ メッセージ取得成功 (content: {content}...)\n")
            return True
        else:
            print(f"❌ メッセージ取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_pin_message(channel_id: str, message_id: str):
    """ピン留めテスト"""
    print(f"=== ピン留めテスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "pinMessage", "channelId": channel_id, "messageId": message_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ ピン留め成功\n")
            return True
        else:
            print(f"❌ ピン留め失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_list_pins(channel_id: str):
    """ピン一覧テスト"""
    print(f"=== ピン一覧テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "listPins", "channelId": channel_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ ピン一覧取得成功 ({count}ピン)\n")
            return True
        else:
            print(f"❌ ピン一覧取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_thread_create(channel_id: str, message_id: str, name: str):
    """スレッド作成テスト"""
    print(f"=== スレッド作成テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "threadCreate", "channelId": channel_id, "messageId": message_id, "name": name},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            thread_id = result.get("data", {}).get("thread_id")
            print(f"✅ スレッド作成成功 (thread_id: {thread_id})\n")
            return thread_id
        else:
            print(f"❌ スレッド作成失敗: {result.get('error')}\n")
            return None
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return None


def test_thread_list(guild_id: str):
    """スレッド一覧テスト"""
    print(f"=== スレッド一覧テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "threadList", "guildId": guild_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ スレッド一覧取得成功 (アクティブスレッド数: {count})\n")
            return True
        else:
            print(f"❌ スレッド一覧取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_thread_reply(thread_id: str, content: str):
    """スレッド返信テスト"""
    print(f"=== スレッド返信テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "threadReply", "threadId": thread_id, "content": content},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ スレッド返信成功\n")
            return True
        else:
            print(f"❌ スレッド返信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_member_info(guild_id: str, user_id: str):
    """メンバー情報テスト"""
    print(f"=== メンバー情報テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "memberInfo", "guildId": guild_id, "userId": user_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            username = result.get("data", {}).get("username")
            print(f"✅ メンバー情報取得成功 (username: {username})\n")
            return True
        else:
            print(f"❌ メンバー情報取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_role_info(guild_id: str):
    """ロール情報テスト"""
    print(f"=== ロール情報テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "roleInfo", "guildId": guild_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ ロール情報取得成功 ({count}ロール)\n")
            return True
        else:
            print(f"❌ ロール情報取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_emoji_list(guild_id: str):
    """絵文字一覧テスト"""
    print(f"=== 絵文字一覧テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "emojiList", "guildId": guild_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ 絵文字一覧取得成功 ({count}絵文字)\n")
            return True
        else:
            print(f"❌ 絵文字一覧取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_channel_info(channel_id: str):
    """チャンネル情報テスト"""
    print(f"=== チャンネル情報テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "channelInfo", "channelId": channel_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            name = result.get("data", {}).get("name")
            print(f"✅ チャンネル情報取得成功 (name: {name})\n")
            return True
        else:
            print(f"❌ チャンネル情報取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_channel_list(guild_id: str):
    """チャンネル一覧テスト"""
    print(f"=== チャンネル一覧テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "channelList", "guildId": guild_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ チャンネル一覧取得成功 ({count}チャンネル)\n")
            return True
        else:
            print(f"❌ チャンネル一覧取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_permissions(channel_id: str):
    """権限テスト"""
    print(f"=== 権限テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "permissions", "channelId": channel_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            perms = result.get("data", {}).get("permissions", {})
            print(f"✅ 権限取得成功 (権限数: {len(perms)})\n")
            return True
        else:
            print(f"❌ 権限取得失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def main():
    print("🧪 discord-bot API フル機能テスト開始\n")

    # ヘルスチェック
    if not test_health():
        print("❌ ヘルスチェックに失敗しました。discord-botが起動しているか確認してください。")
        sys.exit(1)

    # 引数からチャンネルIDとギルドIDを取得
    channel_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CHANNEL_ID
    guild_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_GUILD_ID
    user_id = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_USER_ID

    print(f"📝 チャンネルID: {channel_id}")
    print(f"📝 ギルドID: {guild_id}")
    print(f"📝 ユーザーID: {user_id}\n")

    # 1. メッセージ送信
    message_id = test_send_message(channel_id, "🧪 フル機能テスト from Cinderella discord-bot API")

    if not message_id:
        print("❌ メッセージ送信に失敗したため、テストを中止します。")
        sys.exit(1)

    time.sleep(1)

    # 2. リアクション
    test_react(channel_id, message_id, "✅")

    time.sleep(1)

    # 3. リアクション一覧
    test_reactions_list(channel_id, message_id)

    time.sleep(1)

    # 4. メッセージ編集
    import requests as req
    req.post(
        f"{DISCORD_BOT_API_URL}/v1/discord/action",
        json={"action": "editMessage", "channelId": channel_id, "messageId": message_id, "content": "✅ フル機能テストを編集しました"},
        timeout=10
    )

    time.sleep(1)

    # 5. メッセージ読み取り
    test_read_messages(channel_id, 3)

    time.sleep(1)

    # 6. メッセージ取得
    test_fetch_message(guild_id, channel_id, message_id)

    time.sleep(1)

    # 7. スレッド作成
    thread_id = test_thread_create(channel_id, message_id, "フル機能テストスレッド 🧵")

    if thread_id:
        time.sleep(1)

        # 8. スレッド返信
        test_thread_reply(thread_id, "スレッドへの返信テストです 📝")

    # 9. スレッド一覧
    test_thread_list(guild_id)

    # 10. ピン留め
    test_pin_message(channel_id, message_id)

    time.sleep(1)

    # 11. ピン一覧
    test_list_pins(channel_id)

    # 12. メンバー情報
    test_member_info(guild_id, user_id)

    # 13. ロール情報
    test_role_info(guild_id)

    # 14. 絵文字一覧
    test_emoji_list(guild_id)

    # 15. チャンネル情報
    test_channel_info(channel_id)

    # 16. チャンネル一覧
    test_channel_list(guild_id)

    # 17. 権限
    test_permissions(channel_id)

    print("🎉 すべてのテスト完了！")


if __name__ == "__main__":
    main()
