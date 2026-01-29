#!/usr/bin/env python3
"""
discord-bot API チャンネルハンドラーテスト

Discord操作APIのチャンネル関連機能が正しく動作するか確認します。
10個のチャンネルハンドラーをテストします。
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


# ========================================
# Channel Handlers (10 tests)
# ========================================

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


def test_channel_create(guild_id: str):
    """チャンネル作成テスト"""
    print(f"=== チャンネル作成テスト ===")
    try:
        import random
        channel_name = f"test-channel-{random.randint(1000, 9999)}"
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "channelCreate", "guildId": guild_id, "name": channel_name, "type": "text"},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            new_channel_id = result.get("data", {}).get("channel_id")
            print(f"✅ チャンネル作成成功 (channel_id: {new_channel_id})\n")
            return new_channel_id
        else:
            print(f"❌ チャンネル作成失敗: {result.get('error')}\n")
            return None
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return None


def test_category_create(guild_id: str):
    """カテゴリ作成テスト"""
    print(f"=== カテゴリ作成テスト ===")
    try:
        import random
        category_name = f"テストカテゴリ{random.randint(1000, 9999)}"
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "categoryCreate", "guildId": guild_id, "name": category_name},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            category_id = result.get("data", {}).get("category_id")
            print(f"✅ カテゴリ作成成功 (category_id: {category_id})\n")
            return category_id
        else:
            print(f"❌ カテゴリ作成失敗: {result.get('error')}\n")
            return None
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return None


def test_channel_edit(channel_id: str):
    """チャンネル編集テスト"""
    print(f"=== チャンネル編集テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "channelEdit", "channelId": channel_id, "topic": "編集後のトピック"},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ チャンネル編集成功\n")
            return True
        else:
            print(f"❌ チャンネル編集失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_channel_move(guild_id: str, channel_id: str):
    """チャンネル移動テスト"""
    print(f"=== チャンネル移動テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "channelMove", "guildId": guild_id, "channelId": channel_id, "position": 0},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ チャンネル移動成功\n")
            return True
        else:
            print(f"❌ チャンネル移動失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_channel_delete(channel_id: str):
    """チャンネル削除テスト"""
    print(f"=== チャンネル削除テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "channelDelete", "channelId": channel_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ チャンネル削除成功\n")
            return True
        else:
            print(f"❌ チャンネル削除失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_category_edit(category_id: str):
    """カテゴリ編集テスト"""
    print(f"=== カテゴリ編集テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "categoryEdit", "categoryId": category_id, "position": 1},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ カテゴリ編集成功\n")
            return True
        else:
            print(f"❌ カテゴリ編集失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_category_delete(category_id: str):
    """カテゴリ削除テスト"""
    print(f"=== カテゴリ削除テスト ===")
    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={"action": "categoryDelete", "categoryId": category_id},
            timeout=10
        )
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print(f"✅ カテゴリ削除成功\n")
            return True
        else:
            print(f"❌ カテゴリ削除失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def main():
    """メインテストランナー"""
    print("🧪 discord-bot API チャンネルハンドラーテスト開始\n")
    print("10個のチャンネルハンドラーをテストします\n")

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
    print("📁 Channel Handlers (10 tests)")
    print("="*50 + "\n")

    # 1. チャンネル情報
    if test_channel_info(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 2. チャンネル一覧
    if test_channel_list(guild_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 3. 権限
    if test_permissions(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 4. チャンネル作成
    new_channel_id = test_channel_create(guild_id)
    if new_channel_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 5. カテゴリ作成
    new_category_id = test_category_create(guild_id)
    if new_category_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 6. チャンネル編集
    if new_channel_id and test_channel_edit(new_channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 7. チャンネル移動
    if new_channel_id and test_channel_move(guild_id, new_channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 8. チャンネル削除
    if new_channel_id and test_channel_delete(new_channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 9. カテゴリ編集
    if new_category_id and test_category_edit(new_category_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    time.sleep(1)

    # 10. カテゴリ削除
    if new_category_id and test_category_delete(new_category_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 結果表示
    print("\n" + "="*50)
    print("📊 テスト結果")
    print("="*50)
    print(f"✅ パス: {results['passed']}")
    print(f"❌ 失敗: {results['failed']}")
    print(f"⚠️ スキップ: {results['skipped']}")
    print(f"📋 合計: {results['passed'] + results['failed'] + results['skipped']}/10")

    if results['failed'] == 0:
        print("\n🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
