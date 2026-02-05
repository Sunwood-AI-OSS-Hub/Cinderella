#!/usr/bin/env python3
"""
Discord メンション機能テストスクリプト

Discord Bot APIを使ってメンション付きメッセージを送信し、挙動を確認します。
"""

import requests
import json
import sys
import os
import time
from typing import Optional

# API URL
DISCORD_BOT_API_URL = os.getenv("DISCORD_BOT_API_URL", "http://127.0.0.1:8082")

# デフォルトのチャンネルID、ギルドID、ユーザーID（テスト用）
DEFAULT_CHANNEL_ID = "1466415185282732220"  # テスト用チャンネル
DEFAULT_GUILD_ID = "1188045372526964796"
DEFAULT_USER_ID = "539207222494699520"     # メンションするユーザーID
DEFAULT_ROLE_ID = None                     # ロールID（必要に応じて設定）
DEFAULT_BOT_USER_ID = os.getenv("DISCORD_BOT_USER_ID")  # BotのユーザーID
DEFAULT_MENTION_LOOKBACK = int(os.getenv("MENTION_LOOKBACK", "30"))
DEFAULT_SEND_IF_MISSING = os.getenv("SEND_MENTION_IF_MISSING", "0") == "1"
DEFAULT_ONLY_BOT_MENTION = os.getenv("ONLY_BOT_MENTION", "0") == "1"
DEFAULT_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DEFAULT_MENTION_PROMPT = os.getenv("MENTION_PROMPT", "ping")
DEFAULT_WAIT_SECONDS = int(os.getenv("MENTION_WAIT_SECONDS", "60"))
DEFAULT_POLL_INTERVAL = float(os.getenv("MENTION_POLL_INTERVAL", "2.0"))


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


def test_send_normal_message(channel_id: str):
    """通常のメッセージ送信テスト（メンションなし）"""
    print("=== 通常メッセージ送信テスト ===")

    try:
        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": "🧪 これはテストメッセージです（メンションなし）"
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ 通常メッセージ送信成功 (message_id: {message_id})\n")
            return True
        else:
            print(f"❌ メッセージ送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def read_recent_messages(channel_id: str, limit: int = 20):
    """最近のメッセージを取得"""
    response = requests.post(
        f"{DISCORD_BOT_API_URL}/v1/discord/action",
        json={
            "action": "readMessages",
            "channelId": channel_id,
            "limit": limit
        },
        timeout=20
    )
    result = response.json()
    if not result.get("success"):
        raise RuntimeError(f"readMessages failed: {result.get('error')}")
    return result.get("data", {}).get("messages", [])


def get_webhook_channel_id(webhook_url: str) -> Optional[str]:
    """WebhookのチャンネルIDを取得"""
    try:
        response = requests.get(webhook_url, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        return str(data.get("channel_id")) if data else None
    except Exception:
        return None


def send_webhook_message(webhook_url: str, content: str) -> Optional[str]:
    """Discord Webhookでメッセージ送信"""
    response = requests.post(
        f"{webhook_url}?wait=true",
        json={
            "content": content,
            "allowed_mentions": {"parse": ["users"]}
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        return str(data.get("id")) if data else None
    if response.status_code == 204:
        return None
    return None


def is_bot_mention(content: str, bot_user_id: str) -> bool:
    """Botへのメンションか判定"""
    if not content:
        return False
    return f"<@{bot_user_id}>" in content or f"<@!{bot_user_id}>" in content


def find_latest_mention_index(messages: list, bot_user_id: str):
    """最新のBotメンションのインデックスを返す（なければNone）"""
    for i in range(len(messages) - 1, -1, -1):
        if is_bot_mention(messages[i].get("content", ""), bot_user_id):
            return i
    return None


def find_message_index_by_id(messages: list, message_id: Optional[str]):
    """指定メッセージIDのインデックスを返す（なければNone）"""
    if not message_id:
        return None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("id") == str(message_id):
            return i
    return None


def find_bot_reply_after(messages: list, bot_user_id: str, start_index: int):
    """start_index以降のBot返信を探す"""
    for i in range(start_index + 1, len(messages)):
        author = messages[i].get("author", {})
        if author.get("id") == str(bot_user_id) or author.get("bot"):
            return messages[i]
    return None


def test_check_recent_mention_response(
    channel_id: str,
    bot_user_id: str,
    lookback: int = 30,
    send_if_missing: bool = False
):
    """最近のメンションにBotが返信しているか確認"""
    print("=== Botメンション応答確認 ===")
    print(f"BotユーザーID: {bot_user_id}")
    print(f"取得メッセージ数: {lookback}")

    try:
        messages = read_recent_messages(channel_id, limit=lookback)
    except Exception as e:
        print(f"❌ メッセージ取得失敗: {e}\n")
        return False

    mention_index = find_latest_mention_index(messages, bot_user_id)
    if mention_index is None:
        print("⚠️ 最近のメッセージにBotへのメンションが見つかりません")
        if not send_if_missing:
            print("   SEND_MENTION_IF_MISSING=1 を設定すると自動でメンション送信します\n")
            return False
        print("   自動メンションを送信して確認します")
        if not test_send_bot_mention_and_wait(channel_id, bot_user_id):
            return False
        return True

    mention_message = messages[mention_index]
    print(f"✅ 最新メンション検出 (message_id: {mention_message.get('id')})")
    reply = find_bot_reply_after(messages, bot_user_id, mention_index)
    if reply:
        print(f"✅ Bot返信検出 (message_id: {reply.get('id')})\n")
        return True

    print("❌ Bot返信がまだ見つかりません\n")
    return False


def test_send_bot_mention_and_wait(
    channel_id: str,
    bot_user_id: str,
    webhook_url: Optional[str] = None,
    wait_seconds: int = DEFAULT_WAIT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    prompt: str = DEFAULT_MENTION_PROMPT
):
    """Botにメンションを送って返信を待つ"""
    print("=== Botメンション送信 + 応答待ち ===")
    # Botのon_messageはメンション後の内容が空だとエラー応答になるため、
    # 明示的にプロンプトを付与する。
    content = f"<@{bot_user_id}> {prompt}".strip()
    try:
        sent_id = None
        if webhook_url:
            webhook_channel_id = get_webhook_channel_id(webhook_url)
            if webhook_channel_id:
                channel_id = webhook_channel_id
        if webhook_url:
            sent_id = send_webhook_message(webhook_url, content)
            if sent_id is None:
                print("❌ Webhookメンション送信失敗\n")
                return False
            print(f"✅ Webhookメンション送信成功 (message_id: {sent_id})")
            print(f"📝 WebhookチャンネルID: {channel_id}")
        else:
            response = requests.post(
                f"{DISCORD_BOT_API_URL}/v1/discord/action",
                json={
                    "action": "sendMessage",
                    "channelId": channel_id,
                    "content": content
                },
                timeout=10
            )
            result = response.json()
            if not result.get("success"):
                print(f"❌ メンション送信失敗: {result.get('error')}\n")
                return False
            sent_id = result.get("data", {}).get("message_id")
            print(f"✅ メンション送信成功 (message_id: {sent_id})")
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        try:
            messages = read_recent_messages(channel_id, limit=max(20, DEFAULT_MENTION_LOOKBACK))
            mention_index = find_message_index_by_id(messages, sent_id)
            if mention_index is None:
                mention_index = find_latest_mention_index(messages, bot_user_id)
            if mention_index is not None:
                reply = find_bot_reply_after(messages, bot_user_id, mention_index)
                if reply:
                    print(f"✅ Bot返信検出 (message_id: {reply.get('id')})\n")
                    return True
        except Exception:
            pass
        time.sleep(poll_interval)

    print("❌ 応答待ちタイムアウト\n")
    return False


def test_bot_mention_roundtrip(channel_id: str, bot_user_id: str, webhook_url: Optional[str] = None):
    """Botにメンションを送って反応を確認"""
    if not bot_user_id:
        print("❌ BotユーザーIDが未指定です。DISCORD_BOT_USER_ID か第5引数で指定してください。\n")
        return False
    return test_send_bot_mention_and_wait(channel_id, bot_user_id, webhook_url=webhook_url)


def test_send_user_mention(channel_id: str, user_id: str):
    """ユーザーメンション付きメッセージ送信テスト"""
    print("=== ユーザーメンションテスト ===")
    print(f"メンションするユーザーID: {user_id}")

    try:
        # メンション構文: <@USER_ID>
        content = f"🧪 テストメッセージ <@{user_id}> さん、メンションテストです！"

        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": content
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ ユーザーメンション送信成功 (message_id: {message_id})")
            print(f"   送信内容: {content}\n")
            return True
        else:
            print(f"❌ メンション送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_send_multiple_mentions(channel_id: str, user_ids: list):
    """複数メンション付きメッセージ送信テスト"""
    print("=== 複数メンションテスト ===")
    print(f"メンションするユーザーID: {user_ids}")

    try:
        # 複数のメンション構文
        mentions = " ".join([f"<@{uid}>" for uid in user_ids])
        content = f"🧪 複数メンションテスト {mentions} 皆さん、テストです！"

        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": content
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ 複数メンション送信成功 (message_id: {message_id})")
            print(f"   送信内容: {content}\n")
            return True
        else:
            print(f"❌ 複数メンション送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_send_role_mention(channel_id: str, role_id: str):
    """ロールメンション付きメッセージ送信テスト"""
    print("=== ロールメンションテスト ===")
    print(f"メンションするロールID: {role_id}")

    try:
        # ロールメンション構文: <@&ROLE_ID>
        content = f"🧪 ロールメンションテスト <@&{role_id}> のみなさん、テストです！"

        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": content
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ ロールメンション送信成功 (message_id: {message_id})")
            print(f"   送信内容: {content}\n")
            return True
        else:
            print(f"❌ ロールメンション送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_send_everyone_mention(channel_id: str):
    """@everyone メンションテスト"""
    print("=== @everyone メンションテスト ===")

    try:
        content = "🧪 @everyone メンションテストです @everyone 皆さん、確認してください！"

        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": content
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ @everyone メンション送信成功 (message_id: {message_id})")
            print(f"   送信内容: {content}\n")
            return True
        else:
            print(f"❌ @everyone メンション送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_send_here_mention(channel_id: str):
    """@here メンションテスト"""
    print("=== @here メンションテスト ===")

    try:
        content = "🧪 @here メンションテストです @here オンライン中の皆さん、確認してください！"

        response = requests.post(
            f"{DISCORD_BOT_API_URL}/v1/discord/action",
            json={
                "action": "sendMessage",
                "channelId": channel_id,
                "content": content
            },
            timeout=10
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            message_id = result.get("data", {}).get("message_id")
            print(f"✅ @here メンション送信成功 (message_id: {message_id})")
            print(f"   送信内容: {content}\n")
            return True
        else:
            print(f"❌ @here メンション送信失敗: {result.get('error')}\n")
            return False
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False


def test_mention_with_reply(channel_id: str, user_id: str, reply_to_message_id: str):
    """メンション付き返信テスト"""
    print("=== メンション付き返信テスト ===")
    print(f"返信先メッセージID: {reply_to_message_id}")
    print(f"メンションするユーザーID: {user_id}")

    try:
        content = f"📩 <@{user_id}> さん、これは返信テストです！"

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
            print(f"✅ メンション付き返信成功 (message_id: {message_id})")
            print(f"   送信内容: {content}\n")
            return True, message_id
        else:
            print(f"❌ メンション付き返信失敗: {result.get('error')}\n")
            return False, None
    except Exception as e:
        print(f"❌ 例外発生: {e}\n")
        return False, None


def main():
    """メインテストランナー"""
    print("🧪 Discord メンション機能テスト開始\n")
    print("="*60)

    # 引数からチャンネルID、ギルドID、ユーザーID、ロールIDを取得
    channel_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CHANNEL_ID
    guild_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_GUILD_ID
    user_id = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_USER_ID
    role_id = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_ROLE_ID
    bot_user_id = sys.argv[5] if len(sys.argv) > 5 else DEFAULT_BOT_USER_ID
    webhook_url = DEFAULT_WEBHOOK_URL

    print(f"📝 チャンネルID: {channel_id}")
    print(f"📝 ギルドID: {guild_id}")
    print(f"📝 ユーザーID: {user_id}")
    print(f"📝 BotユーザーID: {bot_user_id if bot_user_id else '未指定'}")
    print(f"📝 Webhook: {'設定済み' if webhook_url else '未設定'}")
    print(f"📝 メンションプロンプト: {DEFAULT_MENTION_PROMPT}")
    if role_id:
        print(f"📝 ロールID: {role_id}")
    else:
        print(f"📝 ロールID: なし（ロールメンションテストはスキップされます）")
    print()

    results = {"passed": 0, "failed": 0, "skipped": 0}
    msg_id = None  # 返信テスト用メッセージID

    # ヘルスチェック
    if not test_health():
        print("❌ ヘルスチェックに失敗しました。discord-botが起動しているか確認してください。")
        sys.exit(1)

    if DEFAULT_ONLY_BOT_MENTION:
        print("="*60)
        print("📨 Botメンション反応テスト（単体）")
        print("="*60 + "\n")
        if test_bot_mention_roundtrip(channel_id, bot_user_id, webhook_url=webhook_url):
            results["passed"] += 1
        else:
            results["failed"] += 1

        print("="*60)
        print("📊 テスト結果")
        print("="*60)
        print(f"✅ パス: {results['passed']}")
        print(f"❌ 失敗: {results['failed']}")
        print(f"⚠️ スキップ: {results['skipped']}")
        total = results['passed'] + results['failed'] + results['skipped']
        print(f"📋 合計: {total}")
        sys.exit(0 if results["failed"] == 0 else 1)

    print("="*60)
    print("📨 メンション機能テスト")
    print("="*60 + "\n")

    # テスト1: 通常メッセージ（メンションなし）
    if test_send_normal_message(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # テスト1.5: Botメンション送信→応答確認（BotユーザーIDが指定されている場合）
    if test_bot_mention_roundtrip(channel_id, bot_user_id, webhook_url=webhook_url):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # テスト2: ユーザーメンション
    success = test_send_user_mention(channel_id, user_id)
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
        msg_id = None

    # テスト3: 複数メンション（同じユーザーを2回指定してテスト）
    multiple_users = [user_id, user_id]  # テスト用に同じユーザーを2回
    if test_send_multiple_mentions(channel_id, multiple_users):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # テスト4: ロールメンション（ロールIDがある場合のみ）
    if role_id:
        if test_send_role_mention(channel_id, role_id):
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        print("=== ロールメンションテスト（スキップ - ロールID未指定） ===")
        print("⚠️ ロールIDが指定されていないためスキップします\n")
        results["skipped"] += 1

    # テスト5: @everyone メンション
    if test_send_everyone_mention(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # テスト6: @here メンション
    if test_send_here_mention(channel_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # テスト7: メンション付き返信（メッセージIDがある場合のみ）
    if msg_id:
        success, _ = test_mention_with_reply(channel_id, user_id, msg_id)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        print("=== メンション付き返信テスト（スキップ - 返信先メッセージなし） ===")
        print("⚠️ 返信先メッセージIDがないためスキップします\n")
        results["skipped"] += 1

    # 結果表示
    print("="*60)
    print("📊 テスト結果")
    print("="*60)
    print(f"✅ パス: {results['passed']}")
    print(f"❌ 失敗: {results['failed']}")
    print(f"⚠️ スキップ: {results['skipped']}")
    total = results['passed'] + results['failed'] + results['skipped']
    print(f"📋 合計: {total}")

    if results['failed'] == 0:
        print("\n🎉 すべてのテストが成功しました！")
        print("\n💡 Discordで実際にメンションが機能しているか確認してください。")
        print("   - ユーザー名が青色でハイライトされる")
        print("   - ロールメンションでロールメンバー全員に通知が届く")
        print("   - @everyone/@hereで該当する全員に通知が届く")
        print("   - 返信でスレッドが表示される")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
