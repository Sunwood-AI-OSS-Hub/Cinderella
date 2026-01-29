"""
メッセージ関連ハンドラー

メッセージ送信、編集、削除、リアクション、スレッド、スタンプ、投票、検索など
"""

import logging
import discord
from pydantic import BaseModel

logger = logging.getLogger(__name__)


async def handle_react(req: BaseModel, bot) -> dict:
    """リアクションを追加"""
    if not req.channelId or not req.messageId or not req.emoji:
        return {"success": False, "error": "channelId, messageId, and emoji are required for react"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        message = await channel.fetch_message(int(req.messageId))
        await message.add_reaction(req.emoji)

        logger.info(f"Reaction added successfully")
        return {"success": True, "data": {"message": "Reaction added"}}
    except Exception as e:
        logger.error(f"Failed to add reaction: {e}")
        return {"success": False, "error": str(e)}


async def handle_reactions(req: BaseModel, bot) -> dict:
    """メッセージのリアクションとユーザー一覧を取得"""
    if not req.channelId or not req.messageId:
        return {"success": False, "error": "channelId and messageId are required for reactions"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

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
                    "name": str(reaction.emoji),
                    "animated": getattr(reaction.emoji, 'animated', False) if hasattr(reaction.emoji, 'animated') else False,
                    "id": str(reaction.emoji.id) if hasattr(reaction.emoji, 'id') and reaction.emoji.id else None
                },
                "count": reaction.count,
                "users": users
            })

        logger.info(f"Reactions retrieved: {len(reactions_data)} reactions")
        return {"success": True, "data": {"reactions": reactions_data, "message_id": req.messageId}}
    except Exception as e:
        logger.error(f"Failed to get reactions: {e}")
        return {"success": False, "error": str(e)}


async def handle_send_message(req: BaseModel, bot) -> dict:
    """メッセージを送信"""
    # to パラメータを解析 (channel:<id> または user:<id>)
    channel_id = req.channelId
    if req.to:
        if req.to.startswith("channel:"):
            channel_id = req.to.split(":")[1]
        elif req.to.startswith("user:"):
            # DMの場合は別途処理が必要
            return {"success": False, "error": "DM not yet supported"}

    if not channel_id:
        return {"success": False, "error": "channelId or to is required"}

    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return {"success": False, "error": f"Channel {channel_id} not found"}

        message = await channel.send(req.content or "")

        logger.info(f"Message sent successfully: {message.id}")
        return {"success": True, "data": {"message_id": str(message.id)}}
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return {"success": False, "error": str(e)}


async def handle_edit_message(req: BaseModel, bot) -> dict:
    """メッセージを編集"""
    if not req.channelId or not req.messageId:
        return {"success": False, "error": "channelId and messageId are required for editMessage"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        message = await channel.fetch_message(int(req.messageId))
        await message.edit(content=req.content or "")

        logger.info(f"Message edited successfully: {message.id}")
        return {"success": True, "data": {"message_id": str(message.id)}}
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return {"success": False, "error": str(e)}


async def handle_delete_message(req: BaseModel, bot) -> dict:
    """メッセージを削除"""
    if not req.channelId or not req.messageId:
        return {"success": False, "error": "channelId and messageId are required for deleteMessage"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        message = await channel.fetch_message(int(req.messageId))
        await message.delete()

        logger.info(f"Message deleted successfully")
        return {"success": True, "data": {"message": "Message deleted"}}
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
        return {"success": False, "error": str(e)}


async def handle_read_messages(req: BaseModel, bot) -> dict:
    """チャンネルの最近のメッセージを読む"""
    if not req.channelId:
        return {"success": False, "error": "channelId is required for readMessages"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

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
        return {"success": True, "data": {"messages": messages, "count": len(messages)}}
    except Exception as e:
        logger.error(f"Failed to read messages: {e}")
        return {"success": False, "error": str(e)}


async def handle_fetch_message(req: BaseModel, bot) -> dict:
    """単一のメッセージを取得"""
    if not req.guildId or not req.channelId or not req.messageId:
        return {"success": False, "error": "guildId, channelId, and messageId are required for fetchMessage"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

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
        return {"success": True, "data": message_data}
    except Exception as e:
        logger.error(f"Failed to fetch message: {e}")
        return {"success": False, "error": str(e)}


async def handle_pin_message(req: BaseModel, bot) -> dict:
    """メッセージをピン留め"""
    if not req.channelId or not req.messageId:
        return {"success": False, "error": "channelId and messageId are required for pinMessage"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        message = await channel.fetch_message(int(req.messageId))
        await message.pin()

        logger.info(f"Message pinned: {message.id}")
        return {"success": True, "data": {"message_id": str(message.id), "pinned": True}}
    except Exception as e:
        logger.error(f"Failed to pin message: {e}")
        return {"success": False, "error": str(e)}


async def handle_list_pins(req: BaseModel, bot) -> dict:
    """ピン留めされたメッセージ一覧を取得"""
    if not req.channelId:
        return {"success": False, "error": "channelId is required for listPins"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

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
        return {"success": True, "data": {"pins": pins_data, "count": len(pins_data)}}
    except Exception as e:
        logger.error(f"Failed to list pins: {e}")
        return {"success": False, "error": str(e)}


async def handle_thread_create(req: BaseModel, bot) -> dict:
    """スレッドを作成"""
    if not req.channelId or not req.messageId or not req.name:
        return {"success": False, "error": "channelId, messageId, and name are required for threadCreate"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        message = await channel.fetch_message(int(req.messageId))
        thread = await message.create_thread(name=req.name)

        # Discordではメッセージからスレッドを作成した場合、
        # スレッドIDはメッセージIDと同じになる
        logger.info(f"Thread created successfully: {thread.id}")
        return {"success": True, "data": {"thread_id": str(thread.id), "name": thread.name}}
    except Exception as e:
        logger.error(f"Failed to create thread: {e}")
        return {"success": False, "error": str(e)}


async def handle_thread_list(req: BaseModel, bot) -> dict:
    """スレッド一覧を取得"""
    if not req.guildId:
        return {"success": False, "error": "guildId is required for threadList"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

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
        return {"success": True, "data": {"threads": thread_list, "count": len(thread_list)}}
    except Exception as e:
        logger.error(f"Failed to list threads: {e}")
        return {"success": False, "error": str(e)}


async def handle_thread_reply(req: BaseModel, bot) -> dict:
    """スレッドに返信"""
    if not req.threadId or not req.content:
        return {"success": False, "error": "threadId and content are required for threadReply"}

    try:
        # fetch_channelを使ってスレッドを取得（get_channelはキャッシュのみ）
        thread = await bot.fetch_channel(int(req.threadId))
        if not thread or not hasattr(thread, 'parent_id'):
            return {"success": False, "error": f"Thread {req.threadId} not found"}

        message = await thread.send(req.content)

        logger.info(f"Thread reply sent successfully: {message.id}")
        return {"success": True, "data": {"message_id": str(message.id), "thread_id": req.threadId}}
    except Exception as e:
        logger.error(f"Failed to reply to thread: {e}")
        return {"success": False, "error": str(e)}


async def handle_sticker(req: BaseModel, bot) -> dict:
    """スタンプを送信"""
    if not req.to:
        return {"success": False, "error": "to parameter is required for sticker"}

    try:
        # to パラメータを解析
        if req.to.startswith("channel:"):
            channel_id = req.to.split(":")[1]
        else:
            return {"success": False, "error": "to must be in format channel:<id>"}

        channel = bot.get_channel(int(channel_id))
        if not channel:
            return {"success": False, "error": f"Channel {channel_id} not found"}

        if not req.stickerIds or len(req.stickerIds) == 0:
            return {"success": False, "error": "stickerIds is required"}

        # スタンプを送信（最大3つまで）
        stickers_to_send = req.stickerIds[:3]
        sticker_objs = []
        for sticker_id in stickers_to_send:
            sticker_obj = bot.get_sticker(int(sticker_id))
            if sticker_obj:
                sticker_objs.append(sticker_obj)

        if sticker_objs:
            # メッセージと一緒にスタンプを送信
            await channel.send(content=req.content, stickers=sticker_objs)

            logger.info(f"Stickers sent successfully: {len(sticker_objs)} stickers")
            return {"success": True, "data": {"sticker_count": len(sticker_objs)}}
        else:
            return {"success": False, "error": "No valid stickers found"}
    except Exception as e:
        logger.error(f"Failed to send stickers: {e}")
        return {"success": False, "error": str(e)}


async def handle_poll(req: BaseModel, bot) -> dict:
    """投票を作成"""
    if not req.to or not req.question:
        return {"success": False, "error": "to and question are required for poll"}

    try:
        # to パラメータを解析
        if req.to.startswith("channel:"):
            channel_id = req.to.split(":")[1]
        else:
            return {"success": False, "error": "to must be in format channel:<id>"}

        channel = bot.get_channel(int(channel_id))
        if not channel:
            return {"success": False, "error": f"Channel {channel_id} not found"}

        if not req.answers or len(req.answers) < 2:
            return {"success": False, "error": "poll must have at least 2 answers"}

        # Discord.py はまだ投票を直接サポートしていないので、
        # 代わりに埋め込みメッセージを作成
        poll_text = f"**📊 {req.question}**\n\n"
        for i, answer in enumerate(req.answers, 1):
            poll_text += f"{i}. {answer}\n"

        if req.durationHours:
            poll_text += f"\n⏱️ 投票期間: {req.durationHours}時間"
        if req.allowMultiselect:
            poll_text += "\n✅ 複数選択可能"

        embed = discord.Embed(
            title="🗳️ 投票",
            description=poll_text,
            color=discord.Color.blue()
        )

        message = await channel.send(content=req.content, embed=embed)

        # 各選択肢にリアクションを追加
        for i in range(len(req.answers)):
            emoji_map = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            if i < len(emoji_map):
                await message.add_reaction(emoji_map[i])

        logger.info(f"Poll created successfully: {message.id}")
        return {"success": True, "data": {
            "message_id": str(message.id),
            "question": req.question,
            "answers": req.answers
        }}
    except Exception as e:
        logger.error(f"Failed to create poll: {e}")
        return {"success": False, "error": str(e)}


async def handle_search_messages(req: BaseModel, bot) -> dict:
    """メッセージを検索"""
    if not req.guildId or not req.searchContent:
        return {"success": False, "error": "guildId and searchContent are required for searchMessages"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        limit = req.limit or 20
        messages = []

        # 検索対象のチャンネルを決定
        channels = []
        if req.channelIds and len(req.channelIds) > 0:
            for channel_id in req.channelIds:
                ch = guild.get_channel(int(channel_id))
                if ch and hasattr(ch, 'history'):
                    channels.append(ch)
        else:
            # 全チャンネルを検索
            channels = [ch for ch in guild.channels if hasattr(ch, 'history')]

        # 各チャンネルでメッセージを検索
        for channel in channels:
            try:
                async for message in channel.history(limit=100):
                    if req.searchContent.lower() in message.content.lower():
                        messages.append({
                            "id": str(message.id),
                            "content": message.content,
                            "author": {
                                "id": str(message.author.id),
                                "username": message.author.name,
                                "display_name": message.author.display_name
                            },
                            "channel_id": str(message.channel.id),
                            "channel_name": message.channel.name,
                            "timestamp": message.created_at.isoformat()
                        })
                        if len(messages) >= limit:
                            break
            except Exception as e:
                logger.warning(f"Failed to search channel {channel.id}: {e}")
                continue

            if len(messages) >= limit:
                break

        # 新しい順にソート
        messages.sort(key=lambda x: x["timestamp"], reverse=True)

        logger.info(f"Messages searched: {len(messages)} messages found")
        return {"success": True, "data": {
            "messages": messages,
            "count": len(messages),
            "query": req.searchContent
        }}
    except Exception as e:
        logger.error(f"Failed to search messages: {e}")
        return {"success": False, "error": str(e)}
