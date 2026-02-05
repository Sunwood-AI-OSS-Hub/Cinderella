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
from discord import app_commands
import requests
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import concurrent.futures
from datetime import datetime
from pathlib import Path
import aiohttp
import aiofiles

# ハンドラーをインポート
from handlers import (
    handle_react, handle_reactions,
    handle_send_message, handle_send_file, handle_edit_message, handle_delete_message,
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

# 議論機能ハンドラーをインポート
from debate_handler import (
    DebateManager,
    process_debate_message,
    handle_debate_command,
    BOT_PERSONALITIES,
    debate_manager,
)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN or not DISCORD_TOKEN.strip():
    raise ValueError("DISCORD_TOKEN is required and cannot be empty")

CINDERELLA_URL = os.getenv("CINDERELLA_URL", "http://cc-api:8080")
API_PORT = int(os.getenv("API_PORT", "8080"))

# メディアディレクトリ設定
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "/app/media"))
# メディアディレクトリが存在しない場合は作成
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

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
logger.info(f"📁 メディア保存先: {MEDIA_DIR}")

intents = discord.Intents.default()
intents.message_content = True
# メンションまたは ! で反応
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents, help_command=None)

# Bot名を保存（起動後に設定される）
BOT_USER_ID = None

# FastAPIアプリケーション
api_app = FastAPI(title="Discord Bot API")


class DiscordActionRequest(BaseModel):
    action: str = Field(..., description="アクション名: react, sendMessage, sendFile, editMessage, deleteMessage, threadCreate, threadList, threadReply, reactions, readMessages, fetchMessage, pinMessage, listPins, memberInfo, roleInfo, emojiList, channelInfo, channelList, permissions, sticker, emojiUpload, stickerUpload, poll, searchMessages, channelCreate, categoryCreate, channelEdit, channelMove, channelDelete, categoryEdit, categoryDelete, voiceStatus, eventList, roleAdd, roleRemove, timeout, kick, ban")
    # 共通パラメータ
    channelId: Optional[str] = Field(None, description="チャンネルID")
    messageId: Optional[str] = Field(None, description="メッセージID")
    guildId: Optional[str] = Field(None, description="ギルドID")
    userId: Optional[str] = Field(None, description="ユーザーID")
    # sendMessage用
    to: Optional[str] = Field(None, description="送信先 (channel:<id> または user:<id>)")
    content: Optional[str] = Field(None, description="メッセージ内容")
    replyTo: Optional[str] = Field(None, description="返信先メッセージID")
    # sendFile用
    filePath: Optional[str] = Field(None, description="送信するファイルパス")
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

    # スラッシュコマンドを同期
    try:
        synced = await bot.tree.sync()
        logger.info(f"📋 スラッシュコマンドを {len(synced)} 個同期しました: {[cmd.name for cmd in synced]}")
    except Exception as e:
        logger.error(f"❌ スラッシュコマンドの同期に失敗: {e}")


@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return

    # Botへのメンション、またはBotへの返信かどうかをチェック
    is_mentioned = bot.user in message.mentions
    is_reply_to_bot = message.reference and message.reference.message_id
    # 追加: 返信先がBotかどうかを確認
    if is_reply_to_bot:
        try:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            is_reply_to_bot = referenced_message.author == bot.user
        except Exception:
            is_reply_to_bot = False

    # Botへのメンションまたは返信の場合のみ、添付ファイルを処理
    if is_mentioned or is_reply_to_bot:
        # ========================================
        # 添付ファイルのダウンロード処理
        # ========================================
        if message.attachments:
            logger.info(f"📎 添付ファイルを検出: {len(message.attachments)} 個")
            logger.info(f"   チャンネル: {message.channel.name} (ID: {message.channel.id})")
            logger.info(f"   送信者: {message.author.display_name} (ID: {message.author.id})")

            downloaded_files = []
            for attachment in message.attachments:
                file_path = await download_attachment(attachment, message)
                if file_path:
                    downloaded_files.append({
                        "name": attachment.filename,
                        "path": file_path,
                        "size": attachment.size
                    })

            # 通知メッセージを送信
            if downloaded_files:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                notification = f"📁 **添付ファイルを保存しました**\n"
                notification += f"⏰ {timestamp}\n"
                notification += f"👤 送信者: {message.author.display_name}\n"
                notification += f"📂 保存先: `/workspace/media`\n\n"

                for i, file_info in enumerate(downloaded_files, 1):
                    # サイズを人間が読みやすい形式に変換
                    size = file_info["size"]
                    if size >= 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    elif size >= 1024:
                        size_str = f"{size / 1024:.2f} KB"
                    else:
                        size_str = f"{size} bytes"

                    # ファイルパスを /workspace/media に変換して表示
                    display_path = file_info['path'].replace('/app/media', '/workspace/media')

                    notification += f"**{i}. {file_info['name']}**\n"
                    notification += f"   - ファイルパス: `{display_path}`\n"
                    notification += f"   - サイズ: {size_str}\n"

                await message.channel.send(notification)
                logger.info(f"📤 通知メッセージを送信しました")

    # 議論中のチャンネルかチェック
    context = debate_manager.get_context(message.channel.id)
    if context:
        # 議論中の場合、他のBotのメッセージに応答
        if message.author.bot:
            logger.info(f"Processing debate message from bot {message.author} in channel {message.channel.id}")
            try:
                await process_debate_message(message, bot, context.personality)
            except Exception as e:
                logger.error(f"Error in debate message processing: {e}", exc_info=True)
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
            # Context-likeオブジェクトを作成してprocess_askを呼ぶ
            class MessageContext:
                def __init__(self, msg):
                    self.message = msg
                    self.channel = msg.channel  # channel属性を追加
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

    # 非同期で処理（タスクへの参照を保持して例外を捕捉）
    # リアクションはprocess_ask内で管理される
    task = bot.loop.create_task(process_ask(ctx, prompt))
    task.add_done_callback(lambda t: t.exception() and logger.error(f"Task error: {t.exception()}"))


@bot.command()
async def debate(ctx, *, topic: str = None):
    """Bot間議論を開始するコマンド

    使用方法:
    !debate <トピック> [--personality=<type>]

    例:
    !debate AIと仕事
    !debate リモートワークの是非 --personality=optimist
    """
    if not topic or not topic.strip():
        await ctx.send("❌ 議論のトピックを入力してね！\n例: `!debate AIと仕事`")
        return

    # パーソナリティを抽出（デフォルトはoptimist）
    personality = "optimist"
    if "--personality=" in topic:
        parts = topic.split("--personality=")
        topic = parts[0].strip()
        personality = parts[1].split()[0].strip()

    # 有効なパーソナリティかチェック
    if personality not in BOT_PERSONALITIES:
        await ctx.send(f"❌ 無効なパーソナリティです: {personality}\n選択肢: {', '.join(BOT_PERSONALITIES.keys())}")
        return

    # リアクションで応答
    await ctx.message.add_reaction("💬")

    # 議論を開始
    try:
        await handle_debate_command(ctx, topic, personality)
    except Exception as e:
        logger.error(f"Error in debate command: {e}", exc_info=True)
        await ctx.send(f"❌ 議論の開始中にエラーが発生しました: {e}")


@bot.command()
async def task(ctx, *, prompt: str = None):
    """Claudeに質問してスレッドで会話するコマンド

    使用方法:
    !task <タスク>

    例:
    !task このリポジトリの構造を説明して
    """
    if not prompt or not prompt.strip():
        await ctx.send("❌ タスク内容が空だよ……何か依頼したいことを入力してね！")
        return

    # 非同期で処理
    task = bot.loop.create_task(process_task(ctx, prompt))
    task.add_done_callback(lambda t: t.exception() and logger.error(f"Task error: {t.exception()}"))


async def process_ask(ctx, prompt: str):
    """Cinderella APIを呼び出して結果を返す
    
    重要: Claude CodeはSKILL.mdに従って、自分でDiscord APIを使ってメッセージを送信する
    discord-botは単なるAPIゲートウェイとして機能し、Claude Codeが直接Discordを操作する
    """
    try:
        logger.info("=" * 60)
        logger.info("📨 [1/5] Discordメッセージを受信")
        logger.info(f"  👤 ユーザー: {ctx.message.author} (ID: {ctx.message.author.id})")
        logger.info(f"  💬 チャンネル: {ctx.channel.name} (ID: {ctx.channel.id})")
        logger.info(f"  📝 プロンプト:\n{prompt[:500]}")
        logger.debug(f"  📝 プロンプト (全体):\n{prompt}")
        logger.info("=" * 60)
        
        # Discordの「入力中...」インジケーターを表示
        logger.info("⏳ [2/5] Discordに'入力中...'を表示")
        async with ctx.channel.typing():
            logger.info("📡 [3/5] cc-api (Claude Code) にリクエスト送信")
            logger.info("  → Claude CodeはSKILL.mdに従ってDiscord APIを使用可能")
            logger.info("  → allowed_tools: ['Read', 'Bash', 'Edit', 'discord']")

            # 直近のチャット履歴を取得（添付ファイルの通知を含むため）
            chat_history = ""
            try:
                async for msg in ctx.channel.history(limit=10):
                    # 履歴をフォーマット（Botのメッセージも含める）
                    chat_history += f"[{msg.created_at.strftime('%H:%M')}] {msg.author.display_name}: {msg.content[:200]}\n"
                chat_history = chat_history.strip()
            except Exception as e:
                logger.warning(f"Failed to fetch chat history: {e}")

            # プロンプトにDiscord操作のための情報を追加
            # Guild IDの安全な取得（DMの場合は'N/A'）
            guild_id = 'N/A'
            if hasattr(ctx.channel, 'guild') and ctx.channel.guild:
                guild_id = ctx.channel.guild.id

            enhanced_prompt = f"""{prompt}

---
【Discord操作情報】
あなたは現在Discord上で動作しています。以下の情報を使用して、必要に応じて使用してください。

- Channel ID: {ctx.channel.id}
- Guild ID: {guild_id}
- User ID: {ctx.message.author.id}
- Message ID: {ctx.message.id}

【直近のチャット履歴】
{chat_history if chat_history else '(なし)'}

"""
            
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{CINDERELLA_URL}/v1/claude/run",
                    json={
                        "prompt": enhanced_prompt,
                        "cwd": "/workspace",
                        "allowed_tools": ["Read", "Bash", "Edit", "discord"],
                        "timeout_sec": 300,
                    },
                    timeout=310,
                ),
            )

        logger.info(f"📥 [4/5] cc-apiからレスポンス受信 (status: {response.status_code})")
        logger.info("  → Claude CodeがDiscord APIを使用して直接メッセージを送信した可能性あり")

        if response.status_code == 200:
            data = response.json()
            result = data["stdout_json"].get("result", "")
            logger.debug(f"Result from API (first 200 chars): {result[:200]}")
            
            if not result:
                logger.info("  → Claude Codeからの応答が空（Discord APIで直接送信済みの可能性）")
                # Claude Codeが既にDiscord APIで送信した場合、ここでは何もしない
                logger.info("=" * 60)
                logger.info("[完了] Claude CodeがDiscord APIで直接送信した可能性あり ✅")
                logger.info("=" * 60)
                return

            # 結果を分割送信（Discordの制限対応）
            # 元のメッセージに返信として送信
            logger.info("📤 [5/5] Claude Codeの応答をDiscordに送信（フォールバック）")
            chunks = [result[i : i + 1900] for i in range(0, len(result), 1900)]
            logger.info(f"  分割数: {len(chunks)} chunk(s)")
            for i, chunk in enumerate(chunks):
                logger.info(f"  送信 chunk {i+1}/{len(chunks)} (length: {len(chunk)})")
                await ctx.send(chunk, reference=ctx.message)
                logger.info(f"  ✓ chunk {i+1} 送信完了")

            # 成功時にリアクションを更新
            await update_reaction(ctx.message, "✅")
            logger.info("=" * 60)
            logger.info("[完了] 処理完了 ✅")
            logger.info("=" * 60)
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
    """リアクションを更新する（新しい絵文字を追加）"""
    try:
        await message.add_reaction(new_emoji)
    except Exception as e:
        logger.error(f"Failed to update reaction: {e}")


async def process_task(ctx, prompt: str):
    """スレッドを作成してCinderella APIを呼び出し、スレッドで会話する

    Claude Codeからの応答はスレッド内に投稿される
    """
    thread = None
    try:
        logger.info("=" * 60)
        logger.info("📨 [1/6] Discordタスクメッセージを受信")

        # スラッシュコマンドの場合は interaction から情報を取得
        if hasattr(ctx, 'interaction'):
            user = ctx.interaction.user
            channel = ctx.interaction.channel
            original_message = ctx.interaction.message
        else:
            user = ctx.message.author
            channel = ctx.channel
            original_message = ctx.message

        logger.info(f"  👤 ユーザー: {user} (ID: {user.id})")
        logger.info(f"  💬 チャンネル: {channel.name} (ID: {channel.id})")
        logger.info(f"  📝 プロンプト:\n{prompt[:500]}")
        logger.debug(f"  📝 プロンプト (全体):\n{prompt}")
        logger.info("=" * 60)

        # リアクションで処理中を示す（元メッセージがある場合のみ）
        if original_message:
            await original_message.add_reaction("🧵")

        # スレッドを作成（スラッシュコマンドの場合はチャンネルに送信してからスレッド）
        logger.info("🧵 [2/6] スレッドを作成")

        if original_message:
            # 元メッセージがある場合は、そこからスレッドを作成
            thread = await original_message.create_thread(
                name=f"📋 タスク: {prompt[:50]}..." if len(prompt) > 50 else f"📋 タスク: {prompt}",
                auto_archive_duration=1440  # 24時間後にアーカイブ
            )
        else:
            # スラッシュコマンドの場合は、まずメッセージを送信してからスレッドを作成
            first_message = await channel.send(f"📋 **タスク**: {prompt}")
            thread = await first_message.create_thread(
                name=f"📋 タスク: {prompt[:50]}..." if len(prompt) > 50 else f"📋 タスク: {prompt}",
                auto_archive_duration=1440
            )

        logger.info(f"  ✅ スレッド作成成功: {thread.id}")

        # 開始メッセージを送信
        await thread.send("⏳ タスクを処理中です……")

        # Discordの「入力中...」インジケーターを表示
        logger.info("⏳ [3/6] cc-api (Claude Code) にリクエスト送信")
        logger.info("  → Claude CodeはSKILL.mdに従ってDiscord APIを使用可能")
        logger.info("  → allowed_tools: ['Read', 'Bash', 'Edit', 'discord']")

        async with thread.typing():
            # 直近のチャット履歴を取得
            chat_history = ""
            try:
                # スレッド内の履歴を取得（現在のスレッドのみ）
                async for msg in thread.history(limit=10):
                    chat_history += f"[{msg.created_at.strftime('%H:%M')}] {msg.author.display_name}: {msg.content[:200]}\n"

                # チャンネルの履歴を取得（スレッド外のメッセージのみ、他のスレッドは除外）
                async for msg in channel.history(limit=5):
                    # スレッドに属するメッセージを除外
                    if not msg.thread:
                        chat_history += f"[{msg.created_at.strftime('%H:%M')}] {msg.author.display_name}: {msg.content[:200]}\n"

                chat_history = chat_history.strip()
            except Exception as e:
                logger.warning(f"Failed to fetch chat history: {e}")

            # プロンプトにDiscord操作のための情報を追加
            guild_id = 'N/A'
            if hasattr(channel, 'guild') and channel.guild:
                guild_id = channel.guild.id

            enhanced_prompt = f"""{prompt}

---
【Discord操作情報】
あなたは現在Discord上で動作しています。以下の情報を使用して、必要に応じて使用してください。

- Channel ID: {channel.id}
- Guild ID: {guild_id}
- User ID: {user.id}
- Message ID: {original_message.id if original_message else 'N/A'}
- Thread ID: {thread.id}

【直近のチャット履歴】
{chat_history if chat_history else '(なし)'}

【重要】
回答は必ずスレッド(Thread ID: {thread.id})内で行ってください。
"""

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{CINDERELLA_URL}/v1/claude/run",
                    json={
                        "prompt": enhanced_prompt,
                        "cwd": "/workspace",
                        "allowed_tools": ["Read", "Bash", "Edit", "discord"],
                        "timeout_sec": 300,
                    },
                    timeout=310,
                ),
            )

        logger.info(f"📥 [4/6] cc-apiからレスポンス受信 (status: {response.status_code})")
        logger.info("  → Claude CodeがDiscord APIを使用して直接メッセージを送信した可能性あり")

        if response.status_code == 200:
            data = response.json()
            result = data["stdout_json"].get("result", "")
            logger.debug(f"Result from API (first 200 chars): {result[:200]}")

            if not result:
                logger.info("  → Claude Codeからの応答が空（Discord APIで直接送信済みの可能性）")
                await thread.send("✅ タスク処理完了（Discord APIで直接応答あり）")
                logger.info("=" * 60)
                logger.info("[完了] Claude CodeがDiscord APIで直接送信した可能性あり ✅")
                logger.info("=" * 60)
                return

            # 結果を分割送信（Discordの制限対応）
            logger.info("📤 [5/6] Claude Codeの応答をスレッドに送信")
            chunks = [result[i : i + 1900] for i in range(0, len(result), 1900)]
            logger.info(f"  分割数: {len(chunks)} chunk(s)")
            for i, chunk in enumerate(chunks):
                logger.info(f"  送信 chunk {i+1}/{len(chunks)} (length: {len(chunk)})")
                await thread.send(chunk)
                logger.info(f"  ✓ chunk {i+1} 送信完了")

            # 成功メッセージ
            await thread.send("✅ タスク処理完了")

            # 元のメッセージのリアクションを更新
            if original_message:
                await update_reaction(original_message, "✅")
            logger.info("=" * 60)
            logger.info("[完了] 処理完了 ✅")
            logger.info("=" * 60)
        else:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", "")
            except Exception as e:
                logger.debug(f"Failed to parse error response as JSON: {e}")
            await thread.send(f"❌ エラー ({response.status_code}): {error_detail or 'APIで問題が発生したみたい'}")
            if original_message:
                await update_reaction(original_message, "❌")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        if thread:
            await thread.send("❌ cc-apiに接続できなかったみたい……Dockerコンテナが動いているか確認してね！")
        if original_message:
            await update_reaction(original_message, "❌")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        if thread:
            await thread.send("⏱️ タイムアウトしちゃった……時間のかかる処理は今のところ無理そう")
        if original_message:
            await update_reaction(original_message, "❌")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        if thread:
            await thread.send(f"❌ 例外発生: {type(e).__name__}")
        if original_message:
            await update_reaction(original_message, "❌")


async def download_attachment(attachment, message):
    """添付ファイルをダウンロードして保存

    Args:
        attachment: DiscordのAttachmentオブジェクト
        message: メッセージオブジェクト（メタデータ用）

    Returns:
        保存したファイルパス、失敗時はNone
    """
    try:
        # タイムスタンプを生成 (YYYYMMDD_HHMMSS)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ファイル名を構築: タイムスタンプ_元のファイル名
        original_filename = attachment.filename
        safe_filename = original_filename.replace(" ", "_").replace("/", "_")
        new_filename = f"{timestamp}_{safe_filename}"

        # 保存先パス
        file_path = MEDIA_DIR / new_filename

        # ファイルをダウンロード（タイムアウト設定）
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(await resp.read())
                else:
                    logger.error(f"HTTPエラー: ステータス {resp.status} でダウンロード失敗: {attachment.url}")
                    return None

        logger.info(f"✅ 添付ファイル保存完了: {new_filename}")
        logger.info(f"   - オリジナル名: {original_filename}")
        logger.info(f"   - サイズ: {attachment.size} bytes")
        logger.info(f"   - Content-Type: {attachment.content_type}")
        logger.info(f"   - 保存先: {file_path}")

        return str(file_path)

    except aiohttp.ClientError as e:
        logger.error(f"HTTPエラー: 添付ファイルのダウンロードに失敗: {e}")
        return None
    except OSError as e:
        logger.error(f"ファイルシステムエラー: 添付ファイルの保存に失敗: {e}")
        return None
    except asyncio.TimeoutError:
        logger.error("ダウンロードがタイムアウトしました")
        return None
    except Exception as e:
        logger.error(f"予期しないエラー: 添付ファイルの保存に失敗: {e}")
        return None


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
• `!task <タスク>` - スレッドでタスクを処理
• `!debate <トピック>` - Bot間議論を開始
• `@BotName <質問>` - メンションだけで質問（「ask」は不要）
• `!ping` - 動作確認
• `!info` - Bot情報

**使用例:**
```
!ask 現在の日時を表示して
!task このリポジトリの構造を説明して
!debate AIと仕事
@Cinderella 今日の天気は？
!ping
```

**議論機能について:**
`!debate` コマンドで2人のBotが議論を行います。
ターン数が5回に達するか、議論が収束すると自動的にまとめが作成されます。

**タスク機能について:**
`!task` コマンドはスレッドを作成して、そこで会話します。
長いタスクや議論が必要な場合に便利です。
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
# スラッシュコマンド
# ========================================

@bot.tree.command(name="task", description="Claudeにタスクを依頼してスレッドで会話します")
@app_commands.describe(prompt="依頼したいタスクや質問を入力してください")
async def task_slash(interaction: discord.Interaction, prompt: str):
    """スラッシュコマンド: /task"""
    # 応答を延期（スレッド作成前にDeferする必要がある）
    await interaction.response.defer()

    # Context-likeオブジェクトを作成してprocess_taskを呼ぶ
    class TaskContext:
        def __init__(self, interaction):
            self.interaction = interaction
            self.message = interaction.message
            self.channel = interaction.channel

        async def send(self, *args, **kwargs):
            return await self.interaction.followup.send(*args, **kwargs)

    ctx = TaskContext(interaction)
    await process_task(ctx, prompt)


@bot.tree.command(name="ask", description="Claudeに質問します")
@app_commands.describe(prompt="質問を入力してください")
async def ask_slash(interaction: discord.Interaction, prompt: str):
    """スラッシュコマンド: /ask"""
    await interaction.response.defer()

    class AskContext:
        def __init__(self, interaction):
            self.interaction = interaction
            self.message = interaction.message
            self.channel = interaction.channel

        async def send(self, *args, **kwargs):
            return await self.interaction.followup.send(*args, **kwargs)

    ctx = AskContext(interaction)
    await process_ask(ctx, prompt)


@bot.tree.command(name="ping", description="動作確認")
async def ping_slash(interaction: discord.Interaction):
    """スラッシュコマンド: /ping"""
    await interaction.response.send_message("pon！……ふふ、生きてるよ")


@bot.tree.command(name="info", description="ボット情報を表示")
async def info_slash(interaction: discord.Interaction):
    """スラッシュコマンド: /info"""
    info_text = f"""
**Cinderella Discord Bot** ✨

🤖 Bot名: {bot.user.display_name}
📡 API: {CINDERELLA_URL}
🔧 許可ツール: Read, Bash, Edit
⏱️ タイムアウト: 300秒
"""
    await interaction.response.send_message(info_text)


@bot.tree.command(name="help", description="ヘルプを表示")
async def help_slash(interaction: discord.Interaction):
    """スラッシュコマンド: /help"""
    help_text = """
**Cinderella Discord Bot** 🔮

**スラッシュコマンド一覧:**
• `/task <タスク>` - スレッドでタスクを処理
• `/ask <質問>` - Claudeに質問する
• `/ping` - 動作確認
• `/info` - Bot情報
• `/help` - ヘルプ

**通常コマンド（!で始まる）:**
• `!ask <質問>` - Claudeに質問する
• `!task <タスク>` - スレッドでタスクを処理
• `!debate <トピック>` - Bot間議論を開始

**メンション:**
• `@BotName <質問>` - メンションだけで質問

**使用例:**
```
/task このリポジトリの構造を説明して
/ask 現在の日時を表示して
!debate AIと仕事
@Cinderella 今日の天気は？
/ping
```

**タスク機能について:**
`/task` コマンドはスレッドを作成して、そこで会話します。
長いタスクや議論が必要な場合に便利です。
"""
    await interaction.response.send_message(help_text)


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
        elif action == "sendFile":
            result = run_async(handle_send_file(req, bot))
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
