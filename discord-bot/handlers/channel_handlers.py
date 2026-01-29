"""
チャンネル関連ハンドラー

チャンネル情報、チャンネル一覧、権限、チャンネル作成/編集/移動/削除、カテゴリ管理など
"""

import logging
import discord
from pydantic import BaseModel

logger = logging.getLogger(__name__)


async def handle_channel_info(req: BaseModel, bot) -> dict:
    """チャンネル情報を取得"""
    if not req.channelId:
        return {"success": False, "error": "channelId is required for channelInfo"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

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
        return {"success": True, "data": base_data}
    except Exception as e:
        logger.error(f"Failed to get channel info: {e}")
        return {"success": False, "error": str(e)}


async def handle_channel_list(req: BaseModel, bot) -> dict:
    """ギルドのチャンネル一覧を取得"""
    if not req.guildId:
        return {"success": False, "error": "guildId is required for channelList"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

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
        return {"success": True, "data": {"channels": channels, "count": len(channels)}}
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
        return {"success": False, "error": str(e)}


async def handle_permissions(req: BaseModel, bot) -> dict:
    """ボットのチャンネル権限を確認"""
    if not req.channelId:
        return {"success": False, "error": "channelId is required for permissions"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        # ボットのメンバーを取得
        bot_member = channel.guild.me if hasattr(channel, 'guild') else None
        if not bot_member:
            return {"success": False, "error": "Could not get bot member"}

        # チャンネルでの権限を確認
        permissions = channel.permissions_for(bot_member)

        perms_data = {}
        for perm, value in permissions:
            perms_data[perm] = value

        logger.info(f"Permissions retrieved for channel {channel.id}")
        return {"success": True, "data": {
            "channel_id": str(channel.id),
            "permissions": perms_data,
            "bot_id": str(bot_member.id)
        }}
    except Exception as e:
        logger.error(f"Failed to get permissions: {e}")
        return {"success": False, "error": str(e)}


async def handle_channel_create(req: BaseModel, bot) -> dict:
    """チャンネルを作成"""
    if not req.guildId or not req.name or not req.type:
        return {"success": False, "error": "guildId, name, and type are required for channelCreate"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        # チャンネルタイプをマッピング
        channel_type_map = {
            "text": discord.ChannelType.text,
            "voice": discord.ChannelType.voice,
            "category": discord.ChannelType.category
        }
        channel_type = channel_type_map.get(req.type.lower(), discord.ChannelType.text)

        # 親カテゴリを取得
        parent = None
        if req.parentId:
            parent = guild.get_channel(int(req.parentId))
            if not parent or parent.type != discord.ChannelType.category:
                return {"success": False, "error": f"Parent category {req.parentId} not found"}

        # チャンネルを作成
        channel = await guild.create_text_channel(
            name=req.name,
            category=parent,
            topic=req.topic,
            position=req.position
        )

        logger.info(f"Channel created successfully: {channel.name} ({channel.id})")
        return {"success": True, "data": {
            "channel_id": str(channel.id),
            "name": channel.name,
            "type": str(channel.type)
        }}
    except Exception as e:
        logger.error(f"Failed to create channel: {e}")
        return {"success": False, "error": str(e)}


async def handle_category_create(req: BaseModel, bot) -> dict:
    """カテゴリを作成"""
    if not req.guildId or not req.name:
        return {"success": False, "error": "guildId and name are required for categoryCreate"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        # カテゴリを作成
        category = await guild.create_category(name=req.name)

        logger.info(f"Category created successfully: {category.name} ({category.id})")
        return {"success": True, "data": {
            "category_id": str(category.id),
            "name": category.name
        }}
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        return {"success": False, "error": str(e)}


async def handle_channel_edit(req: BaseModel, bot) -> dict:
    """チャンネルを編集"""
    if not req.channelId:
        return {"success": False, "error": "channelId is required for channelEdit"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        # 編集パラメータを構築
        kwargs = {}
        if req.name:
            kwargs["name"] = req.name
        if req.topic is not None:
            kwargs["topic"] = req.topic
        if req.position is not None:
            kwargs["position"] = req.position
        if req.nsfw is not None:
            kwargs["nsfw"] = req.nsfw

        # チャンネルを編集
        await channel.edit(**kwargs)

        logger.info(f"Channel edited successfully: {channel.id}")
        return {"success": True, "data": {
            "channel_id": str(channel.id),
            "updated": True
        }}
    except Exception as e:
        logger.error(f"Failed to edit channel: {e}")
        return {"success": False, "error": str(e)}


async def handle_channel_move(req: BaseModel, bot) -> dict:
    """チャンネルを移動"""
    if not req.guildId or not req.channelId:
        return {"success": False, "error": "guildId and channelId are required for channelMove"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        channel = guild.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        # 移動パラメータを構築
        kwargs = {}
        if req.parentId:
            parent = guild.get_channel(int(req.parentId))
            if not parent or parent.type != discord.ChannelType.category:
                return {"success": False, "error": f"Parent category {req.parentId} not found"}
            kwargs["category"] = parent
        if req.position is not None:
            kwargs["position"] = req.position

        # チャンネルを移動
        await channel.edit(**kwargs)

        logger.info(f"Channel moved successfully: {channel.id}")
        return {"success": True, "data": {
            "channel_id": str(channel.id),
            "moved": True
        }}
    except Exception as e:
        logger.error(f"Failed to move channel: {e}")
        return {"success": False, "error": str(e)}


async def handle_channel_delete(req: BaseModel, bot) -> dict:
    """チャンネルを削除"""
    if not req.channelId:
        return {"success": False, "error": "channelId is required for channelDelete"}

    try:
        channel = bot.get_channel(int(req.channelId))
        if not channel:
            return {"success": False, "error": f"Channel {req.channelId} not found"}

        # チャンネルを削除
        await channel.delete()

        logger.info(f"Channel deleted successfully: {req.channelId}")
        return {"success": True, "data": {
            "channel_id": req.channelId,
            "deleted": True
        }}
    except Exception as e:
        logger.error(f"Failed to delete channel: {e}")
        return {"success": False, "error": str(e)}


async def handle_category_edit(req: BaseModel, bot) -> dict:
    """カテゴリを編集"""
    if not req.categoryId:
        return {"success": False, "error": "categoryId is required for categoryEdit"}

    try:
        category = bot.get_channel(int(req.categoryId))
        if not category or category.type != discord.ChannelType.category:
            return {"success": False, "error": f"Category {req.categoryId} not found"}

        # 編集パラメータを構築
        kwargs = {}
        if req.name:
            kwargs["name"] = req.name
        if req.position is not None:
            kwargs["position"] = req.position

        # カテゴリを編集
        await category.edit(**kwargs)

        logger.info(f"Category edited successfully: {category.id}")
        return {"success": True, "data": {
            "category_id": str(category.id),
            "updated": True
        }}
    except Exception as e:
        logger.error(f"Failed to edit category: {e}")
        return {"success": False, "error": str(e)}


async def handle_category_delete(req: BaseModel, bot) -> dict:
    """カテゴリを削除"""
    if not req.categoryId:
        return {"success": False, "error": "categoryId is required for categoryDelete"}

    try:
        category = bot.get_channel(int(req.categoryId))
        if not category or category.type != discord.ChannelType.category:
            return {"success": False, "error": f"Category {req.categoryId} not found"}

        # カテゴリを削除
        await category.delete()

        logger.info(f"Category deleted successfully: {req.categoryId}")
        return {"success": True, "data": {
            "category_id": req.categoryId,
            "deleted": True
        }}
    except Exception as e:
        logger.error(f"Failed to delete category: {e}")
        return {"success": False, "error": str(e)}
