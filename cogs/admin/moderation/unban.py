# ==========================================
# unban.py
# UNBANコマンド
# BAN解除を行い、DM・公開/管理者ログを残す
# ==========================================

import discord
from discord.ext import commands
from discord import app_commands

from cogs.admin.common import send_dm
from cogs.admin.logs.log_embed import public_log, admin_log
from database.db import add_mod_log, get_last_log_id, get_guild_settings


class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unban", description="ユーザーのBANを解除します")
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str
    ):
        guild = interaction.guild

        try:
            user = await self.bot.fetch_user(int(user_id))
        except Exception:
            await interaction.response.send_message(
                "❌ ユーザーIDが正しくありません",
                ephemeral=True
            )
            return

        await guild.unban(user)

        reason = "BAN解除"

        # DBに記録
        add_mod_log(
            guild.id,
            user.id,
            interaction.user.id,
            "UNBAN",
            reason
        )

        # DM送信
        await send_dm(
            user,
            "🔓 BAN解除通知",
            f"サーバー: **{guild.name}**\nあなたのBANが解除されました。"
        )

        log_id = get_last_log_id()
        settings = get_guild_settings(guild.id)

        # ログ送信
        if settings:
            if ch := guild.get_channel(settings["public_log_channel"]):
                await ch.send(embed=public_log(guild, user, "UNBAN"))
            if ch := guild.get_channel(settings["admin_log_channel"]):
                await ch.send(embed=admin_log(
                    guild,
                    interaction.user,
                    user,
                    "UNBAN",
                    reason,
                    log_id
                ))

        await interaction.response.send_message(
            "✅ BANを解除しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Unban(bot))
