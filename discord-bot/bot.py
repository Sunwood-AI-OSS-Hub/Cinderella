import os
import asyncio
import logging
import discord
from discord.ext import commands
import requests

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CINDERELLA_URL = os.getenv("CINDERELLA_URL", "http://cc-api:8080")

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


@bot.event
async def on_ready():
    global BOT_USER_ID
    BOT_USER_ID = bot.user.id
    print(f"{bot.user} が起動しました！✨")
    print(f"Connected to {len(bot.guilds)} guilds")


@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return

    # Botへのメンションをチェック
    if bot.user in message.mentions:
        logger.info(f"Bot mentioned by {message.author}: {message.content[:100]}...")

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
    task.add_done_callback(lambda t: t.exception() and print(f"Task error: {t.exception()}"))


async def process_ask(ctx, prompt: str):
    """Cinderella APIを呼び出して結果を返す"""
    try:
        logger.info(f"Processing ask command with prompt: {prompt[:100]}...")
        loop = asyncio.get_event_loop()
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
            except:
                pass
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


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKENが設定されていません")
    bot.run(DISCORD_TOKEN)
