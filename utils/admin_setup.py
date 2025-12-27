# ==========================================
# admin_setup.py
# /adminコマンドで管理者ロール設定
# ==========================================

import discord
from discord import app_commands, Interaction
from discord.ext import commands
from utils import db, permissions

class AdminSetup(commands.Cog):
    """サーバー管理者ロール設定用Cog"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin", description="管理者ロールを設定")
    @permissions.admin_only()
    @app_commands.describe(role="このサーバーの管理者ロール")
    async def set_admin_role(self, interaction: Interaction, role: discord.Role):
        db.set_admin_role(interaction.guild.id, role.id)
        await interaction.response.send_message(
            f"このサーバーの管理者ロールを **{role.name}** に設定しました",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(AdminSetup(bot))
