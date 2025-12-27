# ==========================================
# ticket_setting.py
# /ticket_setting
# チケット作成パネル設置 + ログ通知
# ==========================================

import discord
from discord.ext import commands
from discord import app_commands

from cogs.tickets.ticket_panel_view import TicketCreateView
from database.db import get_guild_settings
from cogs.admin.logs.log_embed import ticket_panel_log_embed


class TicketSetting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket_setting",
        description="チケット作成パネルを設置します（管理者用）"
    )
    async def ticket_setting(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🎫 サポート",
            description="ボタンからチケットを作成してください。",
            color=discord.Color.blurple(),
        )

        panel_message = await interaction.channel.send(
            embed=embed,
            view=TicketCreateView(),
        )

        # ---------- 管理者ログ ----------
        settings = get_guild_settings(interaction.guild.id)
        if settings and settings["admin_log_channel"]:
            log_ch = interaction.guild.get_channel(
                settings["admin_log_channel"]
            )
            if log_ch:
                await log_ch.send(
                    embed=ticket_panel_log_embed(
                        action="パネル設置",
                        executor=interaction.user,
                        channel=interaction.channel,
                        message_id=panel_message.id,
                    )
                )

        await interaction.response.send_message(
            "✅ チケットパネルを設置しました",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(TicketSetting(bot))
