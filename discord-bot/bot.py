import os
import asyncio
import discord
from discord.ext import commands
import requests

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CINDERELLA_URL = os.getenv("CINDERELLA_URL", "http://cc-api:8080")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command()
async def ask(ctx, *, prompt: str):
    """Claudeに質問するコマンド"""
    await ctx.send("ちょっと待っててね……Claudeに聞いてみる！🔮")

    # 非同期で処理
    asyncio.create_task(process_ask(ctx, prompt))


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
                timeout=300,
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
            await ctx.send(f"❌ エラー: {response.status_code}")

    except requests.exceptions.Timeout:
        await ctx.send("⏱️ タイムアウトしちゃった……時間のかかる処理は今のところ無理そう")
    except Exception as e:
        await ctx.send(f"❌ 例外発生: {e}")


@bot.command()
async def ping(ctx):
    """動作確認用コマンド"""
    await ctx.send("pon！……ふふ、生きてるよ")


@bot.event
async def on_ready():
    print(f"{bot.user} が起動しました！✨")
    print(f"Connected to {len(bot.guilds)} guilds")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKENが設定されていません")
    bot.run(DISCORD_TOKEN)
