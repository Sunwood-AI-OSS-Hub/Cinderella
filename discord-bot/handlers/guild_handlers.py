"""
ギルド関連ハンドラー

メンバー情報、ロール管理、絵文字/スタンプ、ボイスステータス、イベント、モデレーションなど
"""

import logging
import aiohttp
import discord
from datetime import datetime, timedelta
from pydantic import BaseModel

logger = logging.getLogger(__name__)


async def handle_member_info(req: BaseModel, bot) -> dict:
    """メンバー情報を取得"""
    if not req.guildId or not req.userId:
        return {"success": False, "error": "guildId and userId are required for memberInfo"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

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
        return {"success": True, "data": member_data}
    except Exception as e:
        logger.error(f"Failed to get member info: {e}")
        return {"success": False, "error": str(e)}


async def handle_role_info(req: BaseModel, bot) -> dict:
    """ロール情報を取得"""
    if not req.guildId:
        return {"success": False, "error": "guildId is required for roleInfo"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

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
        return {"success": True, "data": {"roles": roles, "count": len(roles)}}
    except Exception as e:
        logger.error(f"Failed to get role info: {e}")
        return {"success": False, "error": str(e)}


async def handle_emoji_list(req: BaseModel, bot) -> dict:
    """カスタム絵文字一覧を取得"""
    if not req.guildId:
        return {"success": False, "error": "guildId is required for emojiList"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

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
        return {"success": True, "data": {"emojis": emojis, "count": len(emojis)}}
    except Exception as e:
        logger.error(f"Failed to list emojis: {e}")
        return {"success": False, "error": str(e)}


async def handle_emoji_upload(req: BaseModel, bot) -> dict:
    """絵文字をアップロード"""
    if not req.guildId or not req.name or not req.mediaUrl:
        return {"success": False, "error": "guildId, name, and mediaUrl are required for emojiUpload"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        # mediaUrlから画像をダウンロード
        async with aiohttp.ClientSession() as session:
            async with session.get(req.mediaUrl) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to download media: {resp.status}"}
                image_data = await resp.read()

        # ロールを解析
        roles = []
        if req.roleIds:
            for role_id in req.roleIds:
                role = guild.get_role(int(role_id))
                if role:
                    roles.append(role)

        # 絵文字をアップロード
        emoji = await guild.create_custom_emoji(
            name=req.name,
            image=image_data,
            roles=roles if roles else None
        )

        logger.info(f"Emoji uploaded successfully: {emoji.name} ({emoji.id})")
        return {"success": True, "data": {
            "emoji_id": str(emoji.id),
            "name": emoji.name,
            "url": str(emoji.url)
        }}
    except Exception as e:
        logger.error(f"Failed to upload emoji: {e}")
        return {"success": False, "error": str(e)}


async def handle_sticker_upload(req: BaseModel, bot) -> dict:
    """スタンプをアップロード"""
    if not req.guildId or not req.name or not req.mediaUrl:
        return {"success": False, "error": "guildId, name, and mediaUrl are required for stickerUpload"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        # mediaUrlから画像をダウンロード
        async with aiohttp.ClientSession() as session:
            async with session.get(req.mediaUrl) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"Failed to download media: {resp.status}"}
                image_data = await resp.read()

        # Discord.pyはio.BytesIOを期待する場合がある
        import io
        sticker = await guild.create_sticker(
            name=req.name,
            description=req.description or "",
            emoji=None,
            file=io.BytesIO(image_data)
        )

        logger.info(f"Sticker uploaded successfully: {sticker.name} ({sticker.id})")
        return {"success": True, "data": {
            "sticker_id": str(sticker.id),
            "name": sticker.name,
            "description": sticker.description
        }}
    except Exception as e:
        logger.error(f"Failed to upload sticker: {e}")
        return {"success": False, "error": str(e)}


async def handle_voice_status(req: BaseModel, bot) -> dict:
    """ボイスステータスを取得"""
    if not req.guildId or not req.userId:
        return {"success": False, "error": "guildId and userId are required for voiceStatus"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        member = await guild.fetch_member(int(req.userId))
        if not member:
            return {"success": False, "error": f"Member {req.userId} not found"}

        # ボイスチャンネルに接続しているか確認
        voice_state = member.voice
        if voice_state and voice_state.channel:
            voice_data = {
                "in_voice": True,
                "channel_id": str(voice_state.channel.id),
                "channel_name": voice_state.channel.name,
                "muted": voice_state.self_mute or voice_state.mute,
                "deafened": voice_state.self_deaf or voice_state.deaf,
                "self_muted": voice_state.self_mute,
                "self_deafened": voice_state.self_deaf,
                "self_video": voice_state.self_stream if hasattr(voice_state, 'self_stream') else False
            }
        else:
            voice_data = {
                "in_voice": False,
                "channel_id": None,
                "channel_name": None
            }

        logger.info(f"Voice status retrieved for user {req.userId}")
        return {"success": True, "data": voice_data}
    except Exception as e:
        logger.error(f"Failed to get voice status: {e}")
        return {"success": False, "error": str(e)}


async def handle_event_list(req: BaseModel, bot) -> dict:
    """イベント一覧を取得"""
    if not req.guildId:
        return {"success": False, "error": "guildId is required for eventList"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        # ギルドのイベントを取得
        events = []
        for event in guild.scheduled_events:
            events.append({
                "id": str(event.id),
                "name": event.name,
                "description": event.description,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "location": event.location if hasattr(event, 'location') else None,
                "status": str(event.status),
                "subscriber_count": event.subscriber_count if hasattr(event, 'subscriber_count') else 0,
                "creator_id": str(event.creator.id) if event.creator else None
            })

        logger.info(f"Events retrieved: {len(events)} events")
        return {"success": True, "data": {
            "events": events,
            "count": len(events)
        }}
    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        return {"success": False, "error": str(e)}


async def handle_role_add(req: BaseModel, bot) -> dict:
    """ロールを追加"""
    if not req.guildId or not req.userId or not req.roleId:
        return {"success": False, "error": "guildId, userId, and roleId are required for roleAdd"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        member = await guild.fetch_member(int(req.userId))
        if not member:
            return {"success": False, "error": f"Member {req.userId} not found"}

        role = guild.get_role(int(req.roleId))
        if not role:
            return {"success": False, "error": f"Role {req.roleId} not found"}

        # ロールを追加
        await member.add_roles(role)

        logger.info(f"Role added to user {req.userId}: {role.name}")
        return {"success": True, "data": {
            "user_id": req.userId,
            "role_id": req.roleId,
            "role_name": role.name,
            "added": True
        }}
    except Exception as e:
        logger.error(f"Failed to add role: {e}")
        return {"success": False, "error": str(e)}


async def handle_role_remove(req: BaseModel, bot) -> dict:
    """ロールを削除"""
    if not req.guildId or not req.userId or not req.roleId:
        return {"success": False, "error": "guildId, userId, and roleId are required for roleRemove"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        member = await guild.fetch_member(int(req.userId))
        if not member:
            return {"success": False, "error": f"Member {req.userId} not found"}

        role = guild.get_role(int(req.roleId))
        if not role:
            return {"success": False, "error": f"Role {req.roleId} not found"}

        # ロールを削除
        await member.remove_roles(role)

        logger.info(f"Role removed from user {req.userId}: {role.name}")
        return {"success": True, "data": {
            "user_id": req.userId,
            "role_id": req.roleId,
            "role_name": role.name,
            "removed": True
        }}
    except Exception as e:
        logger.error(f"Failed to remove role: {e}")
        return {"success": False, "error": str(e)}


async def handle_timeout(req: BaseModel, bot) -> dict:
    """ユーザーをタイムアウト"""
    if not req.guildId or not req.userId or not req.durationMinutes:
        return {"success": False, "error": "guildId, userId, and durationMinutes are required for timeout"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        member = await guild.fetch_member(int(req.userId))
        if not member:
            return {"success": False, "error": f"Member {req.userId} not found"}

        # タイムアウト時間を計算
        timeout_until = datetime.utcnow() + timedelta(minutes=req.durationMinutes)

        # タイムアウトを適用
        await member.edit(timeout=timeout_until, reason=req.reason)

        logger.info(f"User {req.userId} timed out for {req.durationMinutes} minutes")
        return {"success": True, "data": {
            "user_id": req.userId,
            "duration_minutes": req.durationMinutes,
            "timeout_until": timeout_until.isoformat(),
            "reason": req.reason
        }}
    except Exception as e:
        logger.error(f"Failed to timeout user: {e}")
        return {"success": False, "error": str(e)}


async def handle_kick(req: BaseModel, bot) -> dict:
    """ユーザーをキック"""
    if not req.guildId or not req.userId:
        return {"success": False, "error": "guildId and userId are required for kick"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        member = await guild.fetch_member(int(req.userId))
        if not member:
            return {"success": False, "error": f"Member {req.userId} not found"}

        # キックを実行
        await member.kick(reason=req.reason)

        logger.info(f"User {req.userId} kicked from guild")
        return {"success": True, "data": {
            "user_id": req.userId,
            "kicked": True,
            "reason": req.reason
        }}
    except Exception as e:
        logger.error(f"Failed to kick user: {e}")
        return {"success": False, "error": str(e)}


async def handle_ban(req: BaseModel, bot) -> dict:
    """ユーザーをBAN"""
    if not req.guildId or not req.userId:
        return {"success": False, "error": "guildId and userId are required for ban"}

    try:
        guild = bot.get_guild(int(req.guildId))
        if not guild:
            return {"success": False, "error": f"Guild {req.guildId} not found"}

        user = await guild.fetch_member(int(req.userId))
        if not user:
            return {"success": False, "error": f"User {req.userId} not found"}

        # BANを実行
        await guild.ban(
            user,
            reason=req.reason,
            delete_message_days=req.deleteMessageDays or 0
        )

        logger.info(f"User {req.userId} banned from guild")
        return {"success": True, "data": {
            "user_id": req.userId,
            "banned": True,
            "reason": req.reason,
            "delete_message_days": req.deleteMessageDays or 0
        }}
    except Exception as e:
        logger.error(f"Failed to ban user: {e}")
        return {"success": False, "error": str(e)}
