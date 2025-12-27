# ==========================================
# untimeout.py
# TIMEOUT解除コマンド
# タイムアウト解除 + DM + ログ管理
# ==========================================

import discord
from discord.ext import commands
from discord import app_commands

from cogs.admin.common import send_dm
from cogs.admin.logs.log_embed import public_log, admin_log
from database.db import add_mod_log, get_last_log_id, get_guild_settings


class Untimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="untimeout",
        description="ユーザーのタイムアウトを解除します"
    )
    async def untimeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        await member.timeout(None)

        reason = "TIMEOUT解除"

        # DBに記録
        add_mod_log(
            interaction.guild.id,
            member.id,
            interaction.user.id,
            "UNTIMEOUT",
            reason
        )

        # DM送信
        await send_dm(
            member,
            "🔓 タイムアウト解除通知",
            f"サーバー: **{interaction.guild.name}**\n"
            "あなたのタイムアウトは解除されました。"
        )

        log_id = get_last_log_id()
        settings = get_guild_settings(interaction.guild.id)

        # ログ送信
        if settings:
            if ch := interaction.guild.get_channel(settings["public_log_channel"]):
                await ch.send(embed=public_log(
                    interaction.guild,
                    member,
                    "UNTIMEOUT"
                ))
            if ch := interaction.guild.get_channel(settings["admin_log_channel"]):
                await ch.send(embed=admin_log(
                    interaction.guild,
                    interaction.user,
                    member,
                    "UNTIMEOUT",
                    reason,
                    log_id
                ))

        await interaction.response.send_message(
            "✅ タイムアウトを解除しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Untimeout(bot))
