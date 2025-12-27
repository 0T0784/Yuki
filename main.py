# ==========================================
# main.py
# オトBotメイン起動ファイル
# Discord.py v2対応、Cogを非同期でロード
# ==========================================
import os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# ==========================================
# Cogリスト
# ==========================================
cogs = [
    "cogs.general.ping",
    "cogs.general.help",
    "cogs.general.about",
    "cogs.general.stats",
    "cogs.admin.ban",
    "cogs.admin.kick",
    "cogs.admin.timeout",
    "cogs.admin.unban_untimeout",
    "cogs.moderation.moderation",
    "cogs.tickets.ticket_panel",
    "cogs.tickets.ticket_management",
    "cogs.youtube_notification.youtube_notif"
]

# ==========================================
# setup_hookでCogを非同期ロード
# ==========================================
async def setup_hook():
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog loaded: {cog}")
        except Exception as e:
            print(f"[ERROR] Failed to load {cog}: {e}")

bot.setup_hook = setup_hook

# ==========================================
# Bot起動完了イベント
# ==========================================
@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user} (ID: {bot.user.id})")

# ==========================================
# Bot実行
# ==========================================
bot.run(os.environ["BOT_TOKEN"])
