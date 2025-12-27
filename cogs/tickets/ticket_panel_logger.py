# ==========================================
# ticket_panel_logger.py
# チケットパネル削除検知ログ
# ==========================================

import discord
from discord.ext import commands

from database.db import get_guild_settings
from cogs.admin.logs.log_embed import ticket_panel_log_embed


class TicketPanelLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return

        # チケットパネルEmbedか判定
        if not message.embeds:
            return

        embed = message.embeds[0]
        if embed.title != "🎫 サポート":
            return

        settings = get_guild_settings(message.guild.id)
        if not settings or not settings["admin_log_channel"]:
            return

        log_ch = message.guild.get_channel(
            settings["admin_log_channel"]
        )
        if not log_ch:
            return

        await log_ch.send(
            embed=ticket_panel_log_embed(
                action="パネル削除",
                executor=message.author or message.guild.me,
                channel=message.channel,
                message_id=message.id,
            )
        )


async def setup(bot):
    await bot.add_cog(TicketPanelLogger(bot))
