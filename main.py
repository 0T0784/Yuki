# ==========================================
# main.py
# Discord Bot + Cog自動ロード + スリープ防止
# ==========================================

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio

# ------------------------------------------
# 環境変数読み込み
# ------------------------------------------
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SELF_PING_URL = os.environ.get("SELF_PING_URL", "http://localhost:8080")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKENが設定されていません。")

# ------------------------------------------
# Bot初期化
# ------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ------------------------------------------
# Cog自動ロード
# ------------------------------------------
COG_FOLDERS = [
    "cogs.admin.moderation",
    "cogs.general",
    "cogs.tickets",
]

async def load_all_cogs():
    for folder in COG_FOLDERS:
        for filename in os.listdir(folder.replace(".", "/")):
            if filename.endswith(".py") and not filename.startswith("__"):
                ext = f"{folder}.{filename[:-3]}"
                try:
                    await bot.load_extension(ext)
                    print(f"✅ Loaded {ext}")
                except Exception as e:
                    print(f"❌ Failed to load {ext}: {e}")

# ------------------------------------------
# 起動イベント
# ------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot起動完了: {bot.user} (ID: {bot.user.id})")

# ------------------------------------------
# スリープ防止用 Webサーバー
# ------------------------------------------
async def handle(request):
    return web.Response(text="Bot is alive!")

async def run_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("🌐 Webserver started on port 8080")

# ------------------------------------------
# 自己Pingタスク（Bot内で定期アクセス）
# ------------------------------------------
async def self_ping_task():
    import aiohttp
    await bot.wait_until_ready()
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(SELF_PING_URL):
                    pass
            except:
                pass
            await asyncio.sleep(5 * 60)  # 5分ごとにPing

# ------------------------------------------
# Bot起動
# ------------------------------------------
async def main():
    await load_all_cogs()
    # Webサーバー起動
    asyncio.create_task(run_webserver())
    # 自己Ping起動
    asyncio.create_task(self_ping_task())
    await bot.start(BOT_TOKEN)

import asyncio
asyncio.run(main())
