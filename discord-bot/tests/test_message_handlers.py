#!/usr/bin/env python3
"""
discord-bot API メッセージハンドラーテスト

Discord操作APIのメッセージ関連機能が正しく動作するか確認します。
17個のメッセージハンドラーをテストします。
"""

import requests
import json
import time
import sys
import os

DISCORD_BOT_API_URL = os.getenv("DISCORD_BOT_API_URL", "http://127.0.0.1:8082")

# デフォルトのチャンネルIDとギルドID（テスト用）
# テスト用チャンネル: https://discord.com/channels/1188045372526964796/1466415185282732220
DEFAULT_CHANNEL_ID = "1466415185282732220"  # テスト用チャンネル
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


# ========================================
# Message Handlers (16 tests)
# ========================================

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


def test_send_message_reply(channel_id: str, reply_to_message_id: str, content: str):
    """メッセージ返信テスト"""
    print(f"=== メッセージ返信テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": content,
                "replyTo": reply_to_message_id
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ メッセージ返信成功 (message_id: {message_id}, reply_to: {reply_to_message_id})\n")
            return message_id
        else:
            print(f"❌ メッセージ返信失敗: {result.get('error')}\n")
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


def test_edit_message(channel_id: str, message_id: str, content: str):
    """メッセージ編集テスト"""
    print(f"=== メッセージ編集テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "editMessage", "channelId": channel_id, "messageId": message_id, "content": content},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ メッセージ編集成功\n")
            return True
        else:
            print(f"❌ メッセージ編集失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_delete_message(channel_id: str, message_id: str):
    """メッセージ削除テスト"""
    print(f"=== メッセージ削除テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "deleteMessage", "channelId": channel_id, "messageId": message_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ メッセージ削除成功\n")
            return True
        else:
            print(f"❌ メッセージ削除失敗: {result.get('error')}\n")
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


def test_sticker(channel_id: str):
    """スタンプ送信テスト"""
    print(f"=== スタンプ送信テスト ===")
    try:
        # スタンプIDはサーバー固有なので、空のリストでテスト
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "sticker", "to": f"channel:{channel_id}", "content": "スタンプテスト"},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # stickerIdsがない場合はエラーになるが、それもテスト
        if not result.get("success") and "stickerIds" in result.get("error", ""):
            print(f"⚠️ スタンプ送信テスト (stickerIdsなしで想定通りのエラー)\n")
            return True
        elif result.get("success"):
            print(f"✅ スタンプ送信成功\n")
            return True
        else:
            print(f"❌ スタンプ送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_poll(channel_id: str):
    """投票作成テスト"""
    print(f"=== 投票作成テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "poll",
                "to": f"channel:{channel_id}",
                "question": "テスト投票",
                "answers": ["選択肢1", "選択肢2", "選択肢3"],
                "allowMultiselect": False,
                "durationHours": 24,
                "content": "投票テストです"
            },
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ 投票作成成功\n")
            return True
        else:
            print(f"❌ 投票作成失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_search_messages(guild_id: str, channel_id: str):
    """メッセージ検索テスト"""
    print(f"=== メッセージ検索テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "searchMessages",
                "guildId": guild_id,
                "searchContent": "テスト",
                "channelIds": [channel_id],
                "limit": 5
            },
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            count = result.get("data", {}).get("count", 0)
            print(f"✅ メッセージ検索成功 ({count}件ヒット)\n")
            return True
        else:
            print(f"❌ メッセージ検索失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_send_file(channel_id: str):
    """ファイル送信テスト"""
    print(f"=== ファイル送信テスト ===")
    try:
        import subprocess
        import tempfile
        import os

        # テスト用ファイルを作成（discord-botコンテナ内の /workspace/media に）
        test_content = "🧪 sendFile テスト用ファイルです\n" \
                      f"作成時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
                      "これは Cinderella discord-bot API のテストです。"

        # docker exec でコンテナ内にファイルを作成
        container_name = "cinderella-discord-bot-1"
        test_file_path = "/workspace/media/test_sendfile.txt"

        # ファイルを作成
        create_result = subprocess.run(
            ["docker", "exec", container_name, "sh", "-c",
             f"echo '{test_content}' > {test_file_path}"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if create_result.returncode != 0:
            print(f"⚠️ テストファイル作成スキップ: {create_result.stderr}")
            print("   手動でファイルを用意してください\n")
            return False

        print(f"📄 テストファイル作成: {test_file_path}")

        # ファイルを送信
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendFile",
                "channelId": channel_id,
                "filePath": test_file_path,
                "content": "📎 ファイル送信テストです"
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            file_name = result.get("data", {}).get("file_name")
            print(f"✅ ファイル送信成功 (file_name: {file_name})\n")
            return True
        else:
            print(f"❌ ファイル送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_send_image(channel_id: str):
    """画像ファイル送信テスト"""
    print(f"=== 画像ファイル送信テスト ===")
    try:
        import subprocess

        container_name = "cinderella-discord-bot-1"
        test_image_path = "/workspace/media/sample.png"

        # 画像ファイルがコンテナ内にあるか確認
        check_result = subprocess.run(
            ["docker", "exec", container_name, "test", "-f", test_image_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if check_result.returncode != 0:
            # ファイルがなければコピー
            print(f"📥 画像ファイルをコンテナにコピーします...")
            copy_result = subprocess.run(
                ["docker", "cp", "/prj/Cinderella/discord-bot/tests/sample.png",
                 f"{container_name}:{test_image_path}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if copy_result.returncode != 0:
                print(f"⚠️ 画像ファイルコピーに失敗: {copy_result.stderr}")
                print("   テストをスキップします\n")
                return False
            print(f"✅ 画像ファイルをコピーしました: {test_image_path}")
        else:
            print(f"✅ 画像ファイルが存在します: {test_image_path}")

        # 画像を送信
        print(f"📤 画像をDiscordに送信します...")
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendFile",
                "channelId": channel_id,
                "filePath": test_image_path,
                "content": "🖼️ 画像送信テスト (sample.png)"
            },
            timeout=30  # 画像ファイルは大きいのでタイムアウトを長く
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            file_name = result.get("data", {}).get("file_name")
            print(f"✅ 画像送信成功 (file_name: {file_name})\n")
            return True
        else:
            print(f"❌ 画像送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def main():
    """メインテストランナー"""
    print("🧪 discord-bot API メッセージハンドラーテスト開始\n")
    print("19個のメッセージハンドラーをテストします\n")

    # ヘルスチェック
    if not test_health():
        print("❌ ヘルスチェックに失敗しました。discord-botが起動しているか確認してください。")
        sys.exit(1)

    # 引数からチャンネルIDとギルドIDを取得
    channel_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CHANNEL_ID
    guild_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_GUILD_ID

    print(f"📝 チャンネルID: {channel_id}")
    print(f"📝 ギルドID: {guild_id}\n")

    results = {"passed": 0, "failed": 0, "skipped": 0}

    print("="*50)
    print("📨 Message Handlers (19 tests)")
    print("="*50 + "\n")

    # 1. メッセージ送信
    message_id = test_send_message(channel_id, "🧪 メッセージハンドラーテスト from Cinderella discord-bot API")
    if message_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 2. リアクション
    if test_react(channel_id, message_id, "✅"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 3. リアクション一覧
    if test_reactions_list(channel_id, message_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 4. メッセージ編集
    if test_edit_message(channel_id, message_id, "✅ メッセージハンドラーテストを編集しました"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 5. メッセージ読み取り
    if test_read_messages(channel_id, 3):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 6. メッセージ取得
    if test_fetch_message(guild_id, channel_id, message_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 7. スレッド作成
    thread_id = test_thread_create(channel_id, message_id, "メッセージハンドラーテストスレッド 🧵")
    if thread_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 8. スレッド返信
    if thread_id and test_thread_reply(thread_id, "スレッドへの返信テストです 📝"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 9. スレッド一覧
    if test_thread_list(guild_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 10. ピン留め
    if test_pin_message(channel_id, message_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 11. ピン一覧
    if test_list_pins(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 12. スタンプ送信
    if test_sticker(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 13. 投票作成
    if test_poll(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 14. メッセージ検索
    if test_search_messages(guild_id, channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 15. ファイル送信（テキスト）
    if test_send_file(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 16. 画像ファイル送信
    if test_send_image(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 17. メッセージ削除（最後）- スキップして残す
    # if test_delete_message(channel_id, message_id):
    #     results["passed"] += 1
    # else:
    #     results["failed"] += 1
    print("=== メッセージ削除テスト（スキップ - 確認用に残す） ===")
    print("⚠️ メッセージ削除はスキップしました（確認用に残しています）\n")
    results["skipped"] += 1

    time.sleep(1)

    # 18. メッセージ返信（新機能）
    reply_message_id = test_send_message_reply(channel_id, message_id, "📩 これは返信テストです（replyTo機能）")
    if reply_message_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 19. 返信メッセージ削除 - スキップして残す
    # if reply_message_id and test_delete_message(channel_id, reply_message_id):
    #     results["passed"] += 1
    # else:
    #     results["failed"] += 1
    print("=== 返信メッセージ削除テスト（スキップ - 確認用に残す） ===")
    print("⚠️ 返信メッセージ削除はスキップしました（確認用に残しています）\n")
    results["skipped"] += 1

    # 結果表示
    print("\n" + "="*50)
    print("📊 テスト結果")
    print("="*50)
    print(f"✅ パス: {results['passed']}")
    print(f"❌ 失敗: {results['failed']}")
    print(f"⚠️ スキップ: {results['skipped']}")
    print(f"📋 合計: {results['passed'] + results['failed'] + results['skipped']}/19")

    if results['failed'] == 0:
        print("\n🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
