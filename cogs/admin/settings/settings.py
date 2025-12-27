# ==========================================
# config.py
# サーバー管理設定コマンド
#
# ・管理者ロールの指定 / 変更
# ・公開ログチャンネルの指定
# ・管理者専用ログチャンネルの指定
#
# サーバーごとの設定をDBに保存し、
# admin系コマンド全体で参照される
# 中枢設定ファイル
# ==========================================

import discord
from discord.ext import commands
from discord import app_commands

from database.db import save_guild_settings, get_guild_settings

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------
    # /config
    # ------------------------------
    @app_commands.command(
        name="config",
        description="管理Botの初期設定を行います"
    )
    async def config(
        self,
        interaction: discord.Interaction,
        admin_role: discord.Role,
        public_log: discord.TextChannel,
        admin_log: discord.TextChannel
    ):
        # Discord管理者のみ実行可能
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ サーバー管理者のみ実行可能です",
                ephemeral=True
            )
            return

        save_guild_settings(
            guild_id=interaction.guild.id,
            admin_role_id=admin_role.id,
            public_log_channel_id=public_log.id,
            admin_log_channel_id=admin_log.id
        )

        await interaction.response.send_message(
            "✅ 管理Botの設定を保存しました",
            ephemeral=True
        )

    # ------------------------------
    # /config_show
    # ------------------------------
    @app_commands.command(
        name="config_show",
        description="現在の設定を表示します"
    )
    async def config_show(self, interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)

        if not settings:
            await interaction.response.send_message(
                "⚠ まだ設定されていません",
                ephemeral=True
            )
            return

        admin_role_id, public_log_id, admin_log_id = settings

        embed = discord.Embed(
            title="⚙ 管理Bot設定",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="管理者ロール",
            value=f"<@&{admin_role_id}>",
            inline=False
        )
        embed.add_field(
            name="公開ログ",
            value=f"<#{public_log_id}>",
            inline=False
        )
        embed.add_field(
            name="管理者ログ",
            value=f"<#{admin_log_id}>",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
