"""
Cinderella Discord Bot

Discord Bot + FastAPI Server
Claude Code から Discord を操作するための API を提供します
"""

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

# ハンドラーをインポート
from handlers import (
    handle_react, handle_reactions,
    handle_send_message, handle_edit_message, handle_delete_message,
    handle_read_messages, handle_fetch_message,
    handle_pin_message, handle_list_pins,
    handle_thread_create, handle_thread_list, handle_thread_reply,
    handle_sticker, handle_poll, handle_search_messages,
    handle_channel_info, handle_channel_list, handle_permissions,
    handle_channel_create, handle_category_create,
    handle_channel_edit, handle_channel_move, handle_channel_delete,
    handle_category_edit, handle_category_delete,
    handle_member_info, handle_role_info, handle_emoji_list,
    handle_emoji_upload, handle_sticker_upload,
    handle_voice_status, handle_event_list,
    handle_role_add, handle_role_remove,
    handle_timeout, handle_kick, handle_ban,
)
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
    action: str = Field(..., description="アクション名: react, sendMessage, editMessage, deleteMessage, threadCreate, threadList, threadReply, reactions, readMessages, fetchMessage, pinMessage, listPins, memberInfo, roleInfo, emojiList, channelInfo, channelList, permissions, sticker, emojiUpload, stickerUpload, poll, searchMessages, channelCreate, categoryCreate, channelEdit, channelMove, channelDelete, categoryEdit, categoryDelete, voiceStatus, eventList, roleAdd, roleRemove, timeout, kick, ban")
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
    # sticker用
    stickerIds: Optional[list] = Field(None, description="スタンプIDリスト")
    # emojiUpload/stickerUpload用
    mediaUrl: Optional[str] = Field(None, description="メディアURL")
    description: Optional[str] = Field(None, description="説明")
    tags: Optional[list] = Field(None, description="タグリスト")
    roleIds: Optional[list] = Field(None, description="ロールIDリスト")
    # poll用
    question: Optional[str] = Field(None, description="投票の質問")
    answers: Optional[list] = Field(None, description="投票の回答リスト")
    allowMultiselect: Optional[bool] = Field(None, description="複数選択を許可するか")
    durationHours: Optional[int] = Field(None, description="投票時間（時間）")
    # searchMessages用
    searchContent: Optional[str] = Field(None, description="検索する文字列")
    channelIds: Optional[list] = Field(None, description="検索対象チャンネルIDリスト")
    # channelCreate/channelEdit/channelMove用
    type: Optional[str] = Field(None, description="チャンネルタイプ")
    parentId: Optional[str] = Field(None, description="親カテゴリID")
    topic: Optional[str] = Field(None, description="チャンネルトピック")
    position: Optional[int] = Field(None, description="チャンネル位置")
    nsfw: Optional[bool] = Field(None, description="NSFW設定")
    # categoryEdit用
    categoryId: Optional[str] = Field(None, description="カテゴリID")
    # timeout/kick/ban用
    durationMinutes: Optional[int] = Field(None, description="タイムアウト時間（分）")
    reason: Optional[str] = Field(None, description="理由")
    deleteMessageDays: Optional[int] = Field(None, description="削除するメッセージの日数")
    roleId: Optional[str] = Field(None, description="ロールID")


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
        # Message handlers
        if action == "react":
            result = run_async(handle_react(req, bot))
        elif action == "reactions":
            result = run_async(handle_reactions(req, bot))
        elif action == "sendMessage":
            result = run_async(handle_send_message(req, bot))
        elif action == "editMessage":
            result = run_async(handle_edit_message(req, bot))
        elif action == "deleteMessage":
            result = run_async(handle_delete_message(req, bot))
        elif action == "readMessages":
            result = run_async(handle_read_messages(req, bot))
        elif action == "fetchMessage":
            result = run_async(handle_fetch_message(req, bot))
        elif action == "pinMessage":
            result = run_async(handle_pin_message(req, bot))
        elif action == "listPins":
            result = run_async(handle_list_pins(req, bot))
        elif action == "threadCreate":
            result = run_async(handle_thread_create(req, bot))
        elif action == "threadList":
            result = run_async(handle_thread_list(req, bot))
        elif action == "threadReply":
            result = run_async(handle_thread_reply(req, bot))
        elif action == "sticker":
            result = run_async(handle_sticker(req, bot))
        elif action == "poll":
            result = run_async(handle_poll(req, bot))
        elif action == "searchMessages":
            result = run_async(handle_search_messages(req, bot))
        # Channel handlers
        elif action == "channelInfo":
            result = run_async(handle_channel_info(req, bot))
        elif action == "channelList":
            result = run_async(handle_channel_list(req, bot))
        elif action == "permissions":
            result = run_async(handle_permissions(req, bot))
        elif action == "channelCreate":
            result = run_async(handle_channel_create(req, bot))
        elif action == "categoryCreate":
            result = run_async(handle_category_create(req, bot))
        elif action == "channelEdit":
            result = run_async(handle_channel_edit(req, bot))
        elif action == "channelMove":
            result = run_async(handle_channel_move(req, bot))
        elif action == "channelDelete":
            result = run_async(handle_channel_delete(req, bot))
        elif action == "categoryEdit":
            result = run_async(handle_category_edit(req, bot))
        elif action == "categoryDelete":
            result = run_async(handle_category_delete(req, bot))
        # Guild handlers
        elif action == "memberInfo":
            result = run_async(handle_member_info(req, bot))
        elif action == "roleInfo":
            result = run_async(handle_role_info(req, bot))
        elif action == "emojiList":
            result = run_async(handle_emoji_list(req, bot))
        elif action == "emojiUpload":
            result = run_async(handle_emoji_upload(req, bot))
        elif action == "stickerUpload":
            result = run_async(handle_sticker_upload(req, bot))
        elif action == "voiceStatus":
            result = run_async(handle_voice_status(req, bot))
        elif action == "eventList":
            result = run_async(handle_event_list(req, bot))
        elif action == "roleAdd":
            result = run_async(handle_role_add(req, bot))
        elif action == "roleRemove":
            result = run_async(handle_role_remove(req, bot))
        elif action == "timeout":
            result = run_async(handle_timeout(req, bot))
        elif action == "kick":
            result = run_async(handle_kick(req, bot))
        elif action == "ban":
            result = run_async(handle_ban(req, bot))
        else:
            return DiscordActionResponse(success=False, error=f"Unknown action: {action}")

        if result.get("success"):
            return DiscordActionResponse(success=True, data=result.get("data"))
        else:
            return DiscordActionResponse(success=False, error=result.get("error"))
    except concurrent.futures.TimeoutError:
        logger.error(f"Discord action timeout after {timeout}s")
        return DiscordActionResponse(success=False, error=f"Timeout after {timeout}s")
    except Exception as e:
        logger.error(f"Discord action error: {e}", exc_info=True)
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
