import os
import asyncio
import logging
import threading
import discord
from discord.ext import commands
import requests
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import concurrent.futures

# 環境変数の検証強化 - 空文字列もチェック
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN or not DISCORD_TOKEN.strip():
    raise ValueError("DISCORD_TOKEN is required and cannot be empty")

CINDERELLA_URL = os.getenv("CINDERELLA_URL", "http://cc-api:8080")
API_PORT = int(os.getenv("API_PORT", "8080"))

# APIキー認証（設定されていない場合は認証なしで動作）
API_KEY = os.getenv("DISCORD_BOT_API_KEY")

# タイムアウト設定（アクション別に最適化）
DEFAULT_TIMEOUT = 30  # デフォルト30秒
ACTION_TIMEOUTS = {
    "sendMessage": 30,
    "readMessages": 60,  # メッセージ一覧は長めに
    "threadList": 60,
    "reactions": 45,
}

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
# メンションまたは ! で反応
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents, help_command=None)

# Bot名を保存（起動後に設定される）
BOT_USER_ID = None

# FastAPIアプリケーション
api_app = FastAPI(title="Discord Bot API")


class DiscordActionRequest(BaseModel):
    action: str = Field(..., description="アクション名: react, sendMessage, editMessage, deleteMessage, threadCreate, threadList, threadReply, reactions, readMessages, fetchMessage, pinMessage, listPins, memberInfo, roleInfo, emojiList, channelInfo, channelList, permissions")
    # 共通パラメータ
    channelId: Optional[str] = Field(None, description="チャンネルID")
    messageId: Optional[str] = Field(None, description="メッセージID")
    guildId: Optional[str] = Field(None, description="ギルドID")
    userId: Optional[str] = Field(None, description="ユーザーID")
    # sendMessage用
    to: Optional[str] = Field(None, description="送信先 (channel:<id> または user:<id>)")
    content: Optional[str] = Field(None, description="メッセージ内容")
    # react用
    emoji: Optional[str] = Field(None, description="リアクション絵文字")
    # スレッド用
    name: Optional[str] = Field(None, description="スレッド名")
    threadId: Optional[str] = Field(None, description="スレッドID")
    # その他のパラメータ
    limit: Optional[int] = Field(None, description="取得数の上限")


class DiscordActionResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


# ========================================
# Discord Bot イベントとコマンド
# ========================================

@bot.event
async def on_ready():
    global BOT_USER_ID
    BOT_USER_ID = bot.user.id
    logger.info(f"{bot.user} が起動しました！✨")
    logger.info(f"Connected to {len(bot.guilds)} guilds")


@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return

    # Botへのメンションをチェック
    if bot.user in message.mentions:
        logger.info(f"Bot mentioned by {message.author}")

        # メンションを削除してプロンプトを抽出
        content = message.content
        # メンション形式を削除（<@ID> と <@!ID> の両方に対応）
        content = content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '')

        # "ask" コマンドがあれば削除（大文字小文字を区別しない）
        content = content.strip()
        if content.lower().startswith('ask '):
            content = content[4:].strip()
        elif content.lower() == 'ask':
            content = ''

        # プロンプトがある場合のみ処理
        if content:
            await message.add_reaction("⏳")
            # Context-likeオブジェクトを作成してprocess_askを呼ぶ
            class MessageContext:
                def __init__(self, msg):
                    self.message = msg
                async def send(self, *args, **kwargs):
                    return await self.message.channel.send(*args, **kwargs)

            ctx = MessageContext(message)
            await process_ask(ctx, content)
        else:
            await message.channel.send("❌ 質問内容が空だよ……何か聞きたいことを入力してね！")
        return

    # 通常のコマンド処理（!askなど）
    await bot.process_commands(message)


@bot.command()
async def ask(ctx, *, prompt: str = None):
    """Claudeに質問するコマンド"""
    if not prompt or not prompt.strip():
        await ctx.send("❌ 質問内容が空だよ……何か聞きたいことを入力してね！")
        return

    # リアクションで応答
    await ctx.message.add_reaction("⏳")

    # 非同期で処理（タスクへの参照を保持して例外を捕捉）
    task = bot.loop.create_task(process_ask(ctx, prompt))
    task.add_done_callback(lambda t: t.exception() and logger.error(f"Task error: {t.exception()}"))


async def process_ask(ctx, prompt: str):
    """Cinderella APIを呼び出して結果を返す"""
    try:
        logger.info("Processing ask command")
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(
                f"{CINDERELLA_URL}/v1/claude/run",
                json={
                    "prompt": prompt,
                    "cwd": "/workspace",
                    "allowed_tools": ["Read", "Bash", "Edit"],
                    "timeout_sec": 300,
                },
                timeout=310,
            ),
        )

        logger.info(f"API response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            result = data["stdout_json"].get("result", "")
            logger.debug(f"Result from API (first 200 chars): {result[:200]}")
            if not result:
                await ctx.send("……あれ、Claudeからの応答が空だったみたい")
                await update_reaction(ctx.message, "❌")
                return

            # 結果を分割送信（Discordの制限対応）
            chunks = [result[i : i + 1900] for i in range(0, len(result), 1900)]
            logger.info(f"Sending {len(chunks)} chunk(s) to Discord")
            for i, chunk in enumerate(chunks):
                logger.debug(f"Sending chunk {i+1}/{len(chunks)} (length: {len(chunk)})")
                await ctx.send(f"```\n{chunk}\n```")

            # 成功時にリアクションを更新
            await update_reaction(ctx.message, "✅")
        else:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", "")
            except Exception as e:
                logger.debug(f"Failed to parse error response as JSON: {e}")
            await ctx.send(f"❌ エラー ({response.status_code}): {error_detail or 'APIで問題が発生したみたい'}")
            await update_reaction(ctx.message, "❌")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        await ctx.send("❌ cc-apiに接続できなかったみたい……Dockerコンテナが動いているか確認してね！")
        await update_reaction(ctx.message, "❌")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        await ctx.send("⏱️ タイムアウトしちゃった……時間のかかる処理は今のところ無理そう")
        await update_reaction(ctx.message, "❌")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        await ctx.send(f"❌ 例外発生: {type(e).__name__}")
        await update_reaction(ctx.message, "❌")


async def update_reaction(message, new_emoji):
    """リアクションを更新する（⏳を削除して新しい絵文字を追加）"""
    try:
        await message.remove_reaction("⏳", bot.user)
        await message.add_reaction(new_emoji)
    except Exception as e:
        logger.error(f"Failed to update reaction: {e}")


@bot.command()
async def ping(ctx):
    """動作確認用コマンド"""
    await ctx.send("pon！……ふふ、生きてるよ")


@bot.command(name="help")
async def help_command(ctx):
    """ヘルプを表示"""
    help_text = """
**Cinderella Discord Bot** 🔮

**コマンド一覧:**
• `!ask <質問>` - Claudeに質問する
• `@BotName <質問>` - メンションだけで質問（「ask」は不要）
• `!ping` - 動作確認
• `!info` - Bot情報

**使用例:**
```
!ask 現在の日時を表示して
@Cinderella 今日の天気は？
@CA1-Mirelle-Flyio 2+2は？
!ping
```
"""
    await ctx.send(help_text)


@bot.command()
async def info(ctx):
    """Bot情報を表示"""
    info_text = f"""
**Cinderella Discord Bot** ✨

🤖 Bot名: {bot.user.display_name}
📡 API: {CINDERELLA_URL}
🔧 許可ツール: Read, Bash, Edit
⏱️ タイムアウト: 300秒
"""
    await ctx.send(info_text)


# ========================================
# FastAPI エンドポイント（Discord操作用）
# ========================================

async def verify_api_key(x_api_key: str = Header(None)):
    """APIキー認証を行う依存関数

    API_KEYが設定されている場合は認証を要求し、
    設定されていない場合は認証なしで動作する（開発環境用）
    """
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key


def run_async(coro, timeout: int = DEFAULT_TIMEOUT):
    """Botのイベントループで非同期処理を実行

    Args:
        coro: 非同期コルーチン
        timeout: タイムアウト秒数（デフォルト30秒）
    """
    future = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    return future.result(timeout=timeout)


@api_app.get("/health")
async def api_health():
    """ヘルスチェック"""
    return {"ok": True, "bot_ready": bot.is_ready()}


@api_app.post(
    "/v1/discord/action",
    response_model=DiscordActionResponse,
    dependencies=[Depends(verify_api_key)]
)
async def discord_action(req: DiscordActionRequest):
    """Discordアクションを実行（Moltbot互換）

    APIキー認証が必要（DISCORD_BOT_API_KEYが設定されている場合）
    """
    if not bot.is_ready():
        return DiscordActionResponse(success=False, error="Bot is not ready yet")

    action = req.action
    logger.info(f"Discord action: {action}")

    # アクションに応じたタイムアウトを取得
    timeout = ACTION_TIMEOUTS.get(action, DEFAULT_TIMEOUT)
    logger.debug(f"Using timeout: {timeout}s for action: {action}")

    try:
        if action == "react":
            return run_async(handle_react(req), timeout)
        elif action == "sendMessage":
            return run_async(handle_send_message(req), timeout)
        elif action == "editMessage":
            return run_async(handle_edit_message(req), timeout)
        elif action == "deleteMessage":
            return run_async(handle_delete_message(req), timeout)
        elif action == "threadCreate":
            return run_async(handle_thread_create(req), timeout)
        elif action == "threadList":
            return run_async(handle_thread_list(req), timeout)
        elif action == "threadReply":
            return run_async(handle_thread_reply(req), timeout)
        elif action == "reactions":
            return run_async(handle_reactions(req), timeout)
        elif action == "readMessages":
            return run_async(handle_read_messages(req), timeout)
        elif action == "fetchMessage":
            return run_async(handle_fetch_message(req), timeout)
        elif action == "pinMessage":
            return run_async(handle_pin_message(req), timeout)
        elif action == "listPins":
            return run_async(handle_list_pins(req), timeout)
        elif action == "memberInfo":
            return run_async(handle_member_info(req), timeout)
        elif action == "roleInfo":
            return run_async(handle_role_info(req), timeout)
        elif action == "emojiList":
            return run_async(handle_emoji_list(req), timeout)
        elif action == "channelInfo":
            return run_async(handle_channel_info(req), timeout)
        elif action == "channelList":
            return run_async(handle_channel_list(req), timeout)
        elif action == "permissions":
            return run_async(handle_permissions(req), timeout)
        else:
            return DiscordActionResponse(success=False, error=f"Unknown action: {action}")
    except concurrent.futures.TimeoutError:
        logger.error(f"Discord action timeout after {timeout}s")
        return DiscordActionResponse(success=False, error=f"Timeout after {timeout}s")
    except Exception as e:
        logger.error(f"Discord action error: {e}", exc_info=True)
        return DiscordActionResponse(success=False, error=str(e))


async def handle_react(req: DiscordActionRequest) -> DiscordActionResponse:
    """リアクションを追加"""
    if not req.channelId or not req.messageId or not req.emoji:
        return DiscordActionResponse(success=False, error="channelId, messageId, and emoji are required for react")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))
        await message.add_reaction(req.emoji)

        logger.info(f"Reaction added successfully")
        return DiscordActionResponse(success=True, data={"message": "Reaction added"})
    except Exception as e:
        logger.error(f"Failed to add reaction: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_send_message(req: DiscordActionRequest) -> DiscordActionResponse:
    """メッセージを送信"""
    # to パラメータを解析 (channel:<id> または user:<id>)
    channel_id = req.channelId
    if req.to:
        if req.to.startswith("channel:"):
            channel_id = req.to.split(":")[1]
        elif req.to.startswith("user:"):
            # DMの場合は別途処理が必要
            return DiscordActionResponse(success=False, error="DM not yet supported")

    if not channel_id:
        return DiscordActionResponse(success=False, error="channelId or to is required")

    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {channel_id} not found")

        message = await channel.send(req.content or "")

        logger.info(f"Message sent successfully: {message.id}")
        return DiscordActionResponse(success=True, data={"message_id": str(message.id)})
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_edit_message(req: DiscordActionRequest) -> DiscordActionResponse:
    """メッセージを編集"""
    if not req.channelId or not req.messageId:
        return DiscordActionResponse(success=False, error="channelId and messageId are required for editMessage")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))
        await message.edit(content=req.content or "")

        logger.info(f"Message edited successfully: {message.id}")
        return DiscordActionResponse(success=True, data={"message_id": str(message.id)})
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_delete_message(req: DiscordActionRequest) -> DiscordActionResponse:
    """メッセージを削除"""
    if not req.channelId or not req.messageId:
        return DiscordActionResponse(success=False, error="channelId and messageId are required for deleteMessage")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))
        await message.delete()

        logger.info(f"Message deleted successfully")
        return DiscordActionResponse(success=True, data={"message": "Message deleted"})
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_thread_create(req: DiscordActionRequest) -> DiscordActionResponse:
    """スレッドを作成"""
    if not req.channelId or not req.messageId or not req.name:
        return DiscordActionResponse(success=False, error="channelId, messageId, and name are required for threadCreate")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))
        thread = await message.create_thread(name=req.name)

        logger.info(f"Thread created successfully: {thread.id}")
        return DiscordActionResponse(success=True, data={"thread_id": str(thread.id), "name": thread.name})
    except Exception as e:
        logger.error(f"Failed to create thread: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_thread_list(req: DiscordActionRequest) -> DiscordActionResponse:
    """スレッド一覧を取得"""
    if not req.guildId:
        return DiscordActionResponse(success=False, error="guildId is required for threadList")

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return DiscordActionResponse(success=False, error=f"Guild {req.guildId} not found")

        threads = [thread for thread in guild.threads if not thread.archived]

        thread_list = [
            {
                "id": str(thread.id),
                "name": thread.name,
                "parent_id": str(thread.parent_id),
                "message_count": thread.message_count
            }
            for thread in threads
        ]

        logger.info(f"Thread list retrieved: {len(thread_list)} active threads")
        return DiscordActionResponse(success=True, data={"threads": thread_list, "count": len(thread_list)})
    except Exception as e:
        logger.error(f"Failed to list threads: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_thread_reply(req: DiscordActionRequest) -> DiscordActionResponse:
    """スレッドに返信"""
    if not req.threadId or not req.content:
        return DiscordActionResponse(success=False, error="threadId and content are required for threadReply")

    try:
        # スレッドを取得
        thread = bot.get_channel(int(req.threadId))
        if not thread or not hasattr(thread, 'parent_id'):
            return DiscordActionResponse(success=False, error=f"Thread {req.threadId} not found")

        message = await thread.send(req.content)

        logger.info(f"Thread reply sent successfully: {message.id}")
        return DiscordActionResponse(success=True, data={"message_id": str(message.id), "thread_id": req.threadId})
    except Exception as e:
        logger.error(f"Failed to reply to thread: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_reactions(req: DiscordActionRequest) -> DiscordActionResponse:
    """メッセージのリアクションとユーザー一覧を取得"""
    if not req.channelId or not req.messageId:
        return DiscordActionResponse(success=False, error="channelId and messageId are required for reactions")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))

        reactions_data = []
        for reaction in message.reactions:
            users = []
            limit = req.limit or 100
            async for user in reaction.users(limit=limit):
                users.append({
                    "id": str(user.id),
                    "username": user.name,
                    "display_name": user.display_name,
                    "bot": user.bot
                })

            reactions_data.append({
                "emoji": {
                    "name": reaction.emoji,
                    "animated": getattr(reaction.emoji, 'animated', False) if hasattr(reaction.emoji, 'animated') else False,
                    "id": str(reaction.emoji.id) if hasattr(reaction.emoji, 'id') and reaction.emoji.id else None
                },
                "count": reaction.count,
                "users": users
            })

        logger.info(f"Reactions retrieved: {len(reactions_data)} reactions")
        return DiscordActionResponse(success=True, data={"reactions": reactions_data, "message_id": req.messageId})
    except Exception as e:
        logger.error(f"Failed to get reactions: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_read_messages(req: DiscordActionRequest) -> DiscordActionResponse:
    """チャンネルの最近のメッセージを読む"""
    if not req.channelId:
        return DiscordActionResponse(success=False, error="channelId is required for readMessages")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        limit = req.limit or 20
        messages = []
        async for message in channel.history(limit=limit):
            reactions = []
            for reaction in message.reactions:
                reactions.append({
                    "emoji": str(reaction.emoji),
                    "count": reaction.count
                })

            messages.append({
                "id": str(message.id),
                "content": message.content,
                "author": {
                    "id": str(message.author.id),
                    "username": message.author.name,
                    "display_name": message.author.display_name,
                    "bot": message.author.bot
                },
                "timestamp": message.created_at.isoformat(),
                "reactions": reactions
            })

        # 昇順（古い順）に並べ替え
        messages.reverse()

        logger.info(f"Messages retrieved: {len(messages)} messages")
        return DiscordActionResponse(success=True, data={"messages": messages, "count": len(messages)})
    except Exception as e:
        logger.error(f"Failed to read messages: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_fetch_message(req: DiscordActionRequest) -> DiscordActionResponse:
    """単一のメッセージを取得"""
    if not req.guildId or not req.channelId or not req.messageId:
        return DiscordActionResponse(success=False, error="guildId, channelId, and messageId are required for fetchMessage")

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return DiscordActionResponse(success=False, error=f"Guild {req.guildId} not found")

        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))

        reactions = []
        for reaction in message.reactions:
            reactions.append({
                "emoji": str(reaction.emoji),
                "count": reaction.count
            })

        message_data = {
            "id": str(message.id),
            "content": message.content,
            "author": {
                "id": str(message.author.id),
                "username": message.author.name,
                "display_name": message.author.display_name,
                "bot": message.author.bot
            },
            "channel_id": str(message.channel.id),
            "guild_id": str(message.guild.id),
            "timestamp": message.created_at.isoformat(),
            "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
            "reactions": reactions,
            "pinned": message.pinned
        }

        # 参照メッセージがある場合は取得
        if message.reference and message.reference.message_id:
            try:
                ref_message = await channel.fetch_message(message.reference.message_id)
                message_data["reference"] = {
                    "message_id": str(ref_message.id),
                    "content": ref_message.content[:200] if ref_message.content else None,
                    "author": {
                        "id": str(ref_message.author.id),
                        "username": ref_message.author.name
                    }
                }
            except Exception:
                message_data["reference"] = None

        logger.info(f"Message fetched: {message.id}")
        return DiscordActionResponse(success=True, data=message_data)
    except Exception as e:
        logger.error(f"Failed to fetch message: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_pin_message(req: DiscordActionRequest) -> DiscordActionResponse:
    """メッセージをピン留め"""
    if not req.channelId or not req.messageId:
        return DiscordActionResponse(success=False, error="channelId and messageId are required for pinMessage")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        message = await channel.fetch_message(int(req.messageId))
        await message.pin()

        logger.info(f"Message pinned: {message.id}")
        return DiscordActionResponse(success=True, data={"message_id": str(message.id), "pinned": True})
    except Exception as e:
        logger.error(f"Failed to pin message: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_list_pins(req: DiscordActionRequest) -> DiscordActionResponse:
    """ピン留めされたメッセージ一覧を取得"""
    if not req.channelId:
        return DiscordActionResponse(success=False, error="channelId is required for listPins")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        pins = await channel.pins()

        pins_data = []
        for message in pins:
            pins_data.append({
                "id": str(message.id),
                "content": message.content,
                "author": {
                    "id": str(message.author.id),
                    "username": message.author.name,
                    "display_name": message.author.display_name
                },
                "timestamp": message.created_at.isoformat()
            })

        logger.info(f"Pins retrieved: {len(pins_data)} pinned messages")
        return DiscordActionResponse(success=True, data={"pins": pins_data, "count": len(pins_data)})
    except Exception as e:
        logger.error(f"Failed to list pins: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_member_info(req: DiscordActionRequest) -> DiscordActionResponse:
    """メンバー情報を取得"""
    if not req.guildId or not req.userId:
        return DiscordActionResponse(success=False, error="guildId and userId are required for memberInfo")

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return DiscordActionResponse(success=False, error=f"Guild {req.guildId} not found")

        member = await guild.fetch_member(int(req.userId))

        roles = []
        for role in member.roles:
            roles.append({
                "id": str(role.id),
                "name": role.name,
                "color": str(role.color),
                "position": role.position
            })

        member_data = {
            "id": str(member.id),
            "username": member.name,
            "display_name": member.display_name,
            "bot": member.bot,
            "avatar_url": member.avatar.url if member.avatar else member.default_avatar.url,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "roles": roles,
            "premium_since": member.premium_since.isoformat() if member.premium_since else None,
            "pending": member.pending if hasattr(member, 'pending') else False
        }

        logger.info(f"Member info retrieved: {member.id}")
        return DiscordActionResponse(success=True, data=member_data)
    except Exception as e:
        logger.error(f"Failed to get member info: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_role_info(req: DiscordActionRequest) -> DiscordActionResponse:
    """ロール情報を取得"""
    if not req.guildId:
        return DiscordActionResponse(success=False, error="guildId is required for roleInfo")

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return DiscordActionResponse(success=False, error=f"Guild {req.guildId} not found")

        roles = []
        for role in guild.roles:
            roles.append({
                "id": str(role.id),
                "name": role.name,
                "color": str(role.color),
                "hoist": role.hoist,
                "position": role.position,
                "permissions": str(role.permissions.value),
                "managed": role.managed,
                "mentionable": role.mentionable,
                "member_count": len(role.members)
            })

        # position順にソート（高い順）
        roles.sort(key=lambda x: x["position"], reverse=True)

        logger.info(f"Role info retrieved: {len(roles)} roles")
        return DiscordActionResponse(success=True, data={"roles": roles, "count": len(roles)})
    except Exception as e:
        logger.error(f"Failed to get role info: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_emoji_list(req: DiscordActionRequest) -> DiscordActionResponse:
    """カスタム絵文字一覧を取得"""
    if not req.guildId:
        return DiscordActionResponse(success=False, error="guildId is required for emojiList")

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return DiscordActionResponse(success=False, error=f"Guild {req.guildId} not found")

        emojis = []
        for emoji in guild.emojis:
            emojis.append({
                "id": str(emoji.id),
                "name": emoji.name,
                "animated": emoji.animated,
                "available": emoji.available,
                "url": str(emoji.url)
            })

        logger.info(f"Emoji list retrieved: {len(emojis)} emojis")
        return DiscordActionResponse(success=True, data={"emojis": emojis, "count": len(emojis)})
    except Exception as e:
        logger.error(f"Failed to list emojis: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_channel_info(req: DiscordActionRequest) -> DiscordActionResponse:
    """チャンネル情報を取得"""
    if not req.channelId:
        return DiscordActionResponse(success=False, error="channelId is required for channelInfo")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        base_data = {
            "id": str(channel.id),
            "name": channel.name,
            "type": str(channel.type),
            "position": channel.position
        }

        # テキストチャンネルの場合
        if hasattr(channel, 'topic'):
            base_data["topic"] = channel.topic
            base_data["nsfw"] = channel.nsfw
            base_data["slowmode_delay"] = channel.slowmode_delay

        # カテゴリ情報
        if hasattr(channel, 'category') and channel.category:
            base_data["category"] = {
                "id": str(channel.category.id),
                "name": channel.category.name
            }

        # スレッドの場合
        if hasattr(channel, 'parent_id') and channel.parent_id:
            base_data["parent_id"] = str(channel.parent_id)
            base_data["message_count"] = channel.message_count if hasattr(channel, 'message_count') else None
            base_data["owner_id"] = str(channel.owner_id) if hasattr(channel, 'owner_id') else None

        logger.info(f"Channel info retrieved: {channel.id}")
        return DiscordActionResponse(success=True, data=base_data)
    except Exception as e:
        logger.error(f"Failed to get channel info: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_channel_list(req: DiscordActionRequest) -> DiscordActionResponse:
    """ギルドのチャンネル一覧を取得"""
    if not req.guildId:
        return DiscordActionResponse(success=False, error="guildId is required for channelList")

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return DiscordActionResponse(success=False, error=f"Guild {req.guildId} not found")

        channels = []
        for channel in guild.channels:
            base_data = {
                "id": str(channel.id),
                "name": channel.name,
                "type": str(channel.type),
                "position": channel.position
            }

            # テキストチャンネルの場合
            if hasattr(channel, 'topic'):
                base_data["topic"] = channel.topic
                base_data["nsfw"] = channel.nsfw

            # カテゴリ情報
            if hasattr(channel, 'category') and channel.category:
                base_data["category_id"] = str(channel.category.id)
                base_data["category_name"] = channel.category.name

            # スレッドの場合
            if hasattr(channel, 'parent_id') and channel.parent_id:
                base_data["parent_id"] = str(channel.parent_id)

            channels.append(base_data)

        # position順にソート
        channels.sort(key=lambda x: x["position"])

        logger.info(f"Channel list retrieved: {len(channels)} channels")
        return DiscordActionResponse(success=True, data={"channels": channels, "count": len(channels)})
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
        return DiscordActionResponse(success=False, error=str(e))


async def handle_permissions(req: DiscordActionRequest) -> DiscordActionResponse:
    """ボットのチャンネル権限を確認"""
    if not req.channelId:
        return DiscordActionResponse(success=False, error="channelId is required for permissions")

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return DiscordActionResponse(success=False, error=f"Channel {req.channelId} not found")

        # ボットのメンバーを取得
        bot_member = channel.guild.me if hasattr(channel, 'guild') else None
        if not bot_member:
            return DiscordActionResponse(success=False, error="Could not get bot member")

        # チャンネルでの権限を確認
        permissions = channel.permissions_for(bot_member)

        perms_data = {}
        for perm, value in permissions:
            perms_data[perm] = value

        logger.info(f"Permissions retrieved for channel {channel.id}")
        return DiscordActionResponse(success=True, data={
            "channel_id": str(channel.id),
            "permissions": perms_data,
            "bot_id": str(bot_member.id)
        })
    except Exception as e:
        logger.error(f"Failed to get permissions: {e}")
        return DiscordActionResponse(success=False, error=str(e))


# ========================================
# FastAPIサーバーを別スレッドで起動
# ========================================

def run_api():
    """FastAPIサーバーを別スレッドで実行"""
    logger.info(f"Starting API server on port {API_PORT}")
    uvicorn.run(api_app, host="0.0.0.0", port=API_PORT, log_level="info")


# ========================================
# メイン処理
# ========================================

if __name__ == "__main__":
    # FastAPIサーバーを別スレッドで起動
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Discord Botを起動
    bot.run(DISCORD_TOKEN)
