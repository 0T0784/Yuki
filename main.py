# ==========================================
# main.py
# Discord Bot + Cog自動ロード + スリープ防止
# ==========================================

import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Cogをロード
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

async def load_cogs():
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog loaded: {cog}")
        except Exception as e:
            print(f"[ERROR] Failed to load {cog}: {e}")

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user} (ID: {bot.user.id})")

bot.loop.create_task(load_cogs())
bot.run(os.environ["BOT_TOKEN"])
