# ==========================================
# main.py
# Discord Bot 起動用メインファイル
# Cogロード + Slashコマンド同期対応
# Koyeb用HealthCheck対応済み
# ==========================================
import os
import asyncio
from discord.ext import commands
import discord

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# ==========================================
# Cogを非同期でロード
# ==========================================
async def load_cogs():
    for extension in [
        "cogs.admin",
        "cogs.moderation",
        "cogs.general",
        "cogs.tickets",
        "cogs.youtube_notification",
        "cogs.stats"
    ]:
        try:
            await bot.load_extension(extension)
            print(f"[INFO] Cog loaded: {extension}")
        except Exception as e:
            print(f"[ERROR] Failed to load {extension}: {e}")

# ==========================================
# setup_hook で Cogロード + コマンド同期
# ==========================================
@bot.event
async def setup_hook():
    # Cogをロード
    await load_cogs()

    # グローバル同期（サーバーにSlashコマンドを登録）
    try:
        await bot.tree.sync()
        print("[INFO] Application commands synced globally!")
    except Exception as e:
        print(f"[ERROR] Failed to sync commands: {e}")

# ==========================================
# HealthCheck用簡易Webサーバー
# ==========================================
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!", 200

# 別スレッドでFlaskを起動
import threading
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# ==========================================
# Botを起動
# ==========================================
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN が設定されていません！")
    bot.run(token)
