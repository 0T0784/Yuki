# ==========================================
# main.py
# Koyeb対応：即起動 + バックグラウンドコマンド同期
# ==========================================
import os
import asyncio
import discord
from discord.ext import commands
from utils import db  # db.pyなどを使用する場合

# Botの設定
intents = discord.Intents.default()
intents.members = True  # メンバー関連の処理がある場合

bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    application_id=int(os.environ.get("APP_ID", 0))  # App ID必須
)

# ==========================================
# Cog読み込み関数
# ==========================================
async def load_cogs():
    cogs = [
        "cogs.admin",
        "cogs.moderation",
        "cogs.tickets",
        "cogs.youtube_notification",
        "cogs.general",
        "cogs.stats"
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog loaded: {cog}")
        except Exception as e:
            print(f"[ERROR] Failed to load {cog}: {e}")

# ==========================================
# コマンド同期関数（バックグラウンド）
# ==========================================
async def sync_commands_background():
    await bot.wait_until_ready()
    try:
        # テストサーバーIDを指定すると即反映される
        TEST_GUILD_ID = int(os.environ.get("TEST_GUILD_ID", 0))
        if TEST_GUILD_ID:
            guild = discord.Object(id=TEST_GUILD_ID)
            await bot.tree.sync(guild=guild)
            print("[INFO] Commands synced to test server!")
        # グローバル同期もバックグラウンドで
        await bot.tree.sync()
        print("[INFO] Global commands synced!")
    except Exception as e:
        print(f"[ERROR] Failed to sync commands: {e}")

# ==========================================
# 起動時イベント
# ==========================================
@bot.event
async def on_ready():
    print(f"[INFO] Bot is ready: {bot.user} (ID: {bot.user.id})")
    print(f"[INFO] Servers: {[guild.name for guild in bot.guilds]}")

# ==========================================
# main処理
# ==========================================
async def main():
    # Cog読み込み
    await load_cogs()
    # コマンド同期をバックグラウンドで
    bot.loop.create_task(sync_commands_background())
    # Bot起動
    await bot.start(os.environ["BOT_TOKEN"])

# 非同期メインを実行
asyncio.run(main())
