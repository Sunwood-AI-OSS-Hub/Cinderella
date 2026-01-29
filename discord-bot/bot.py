import os
import asyncio
import discord
from discord.ext import commands
import requests

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CINDERELLA_URL = os.getenv("CINDERELLA_URL", "http://cc-api:8080")

intents = discord.Intents.default()
intents.message_content = True
# メンションまたは ! で反応
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)


@bot.command()
async def ask(ctx, *, prompt: str = None):
    """Claudeに質問するコマンド"""
    if not prompt or not prompt.strip():
        await ctx.send("❌ 質問内容が空だよ……何か聞きたいことを入力してね！")
        return

    await ctx.send("ちょっと待っててね……Claudeに聞いてみる！🔮")

    # 非同期で処理（タスクへの参照を保持）
    bot.loop.create_task(process_ask(ctx, prompt))


async def process_ask(ctx, prompt: str):
    """Cinderella APIを呼び出して結果を返す"""
    try:
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

        if response.status_code == 200:
            data = response.json()
            result = data["stdout_json"].get("result", "")
            if not result:
                await ctx.send("……あれ、Claudeからの応答が空だったみたい")
                return

            # 結果を分割送信（Discordの制限対応）
            for chunk in [result[i : i + 1900] for i in range(0, len(result), 1900)]:
                await ctx.send(f"```\n{chunk}\n```")
        else:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", "")
            except:
                pass
            await ctx.send(f"❌ エラー ({response.status_code}): {error_detail or 'APIで問題が発生したみたい'}")

    except requests.exceptions.ConnectionError:
        await ctx.send("❌ cc-apiに接続できなかったみたい……Dockerコンテナが動いているか確認してね！")
    except requests.exceptions.Timeout:
        await ctx.send("⏱️ タイムアウトしちゃった……時間のかかる処理は今のところ無理そう")
    except Exception as e:
        await ctx.send(f"❌ 例外発生: {type(e).__name__}")


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
• `!ask <質問>` または `@BotName ask <質問>` - Claudeに質問する
• `!ping` または `@BotName ping` - 動作確認
• `!info` または `@BotName info` - Bot情報

**使用例:**
```
!ask 現在の日時を表示して
@Cinderella ask 今日の天気は？
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


@bot.event
async def on_ready():
    print(f"{bot.user} が起動しました！✨")
    print(f"Connected to {len(bot.guilds)} guilds")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKENが設定されていません")
    bot.run(DISCORD_TOKEN)
