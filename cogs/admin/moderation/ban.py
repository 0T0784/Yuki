# ==========================================
# ban.py
# BANコマンド
# ==========================================

import discord
from discord.ext import commands
from discord import app_commands

from cogs.admin.common import send_dm
from cogs.admin.logs.log_embed import public_log, admin_log
from cogs.admin.moderation.reason_select import ReasonView
from database.db import add_mod_log, get_last_log_id, get_guild_settings


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="ユーザーをBANします")
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        view = ReasonView()
        await interaction.response.send_message(
            "処罰理由を選択してください",
            view=view,
            ephemeral=True
        )

        await view.wait()
        reason = view.reason or "未指定"

        await member.ban(reason=reason)

        add_mod_log(
            interaction.guild.id,
            member.id,
            interaction.user.id,
            "BAN",
            reason
        )

        await send_dm(
            member,
            "🔨 BAN通知",
            f"サーバー: **{interaction.guild.name}**\n理由: **{reason}**"
        )

        log_id = get_last_log_id()
        settings = get_guild_settings(interaction.guild.id)

        if settings:
            if ch := interaction.guild.get_channel(settings["public_log_channel"]):
                await ch.send(embed=public_log(interaction.guild, member, "BAN"))
            if ch := interaction.guild.get_channel(settings["admin_log_channel"]):
                await ch.send(embed=admin_log(
                    interaction.guild,
                    interaction.user,
                    member,
                    "BAN",
                    reason,
                    log_id
                ))

        await interaction.followup.send("✅ BANしました", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ban(bot))
