# ==========================================
# help.py
# HELPコマンド（権限別表示）
#
# ・一般ユーザーには一般コマンドのみ表示
# ・管理権限を持つユーザーには管理コマンドも表示
# ・Embed 1枚で自動切り替え
# ==========================================

import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Botの使い方を表示します（権限別）"
    )
    async def help(self, interaction: discord.Interaction):
        user = interaction.user
        perms = user.guild_permissions

        # ------------------------------
        # 管理権限チェック
        # ------------------------------
        is_moderator = (
            perms.administrator
            or perms.ban_members
            or perms.moderate_members
        )

        embed = discord.Embed(
            title="📖 コマンド一覧",
            color=discord.Color.blurple()
        )

        # ------------------------------
        # 一般コマンド（全員）
        # ------------------------------
        embed.add_field(
            name="🔧 一般コマンド",
            value=(
                "`/ping` - Botの応答速度を確認\n"
                "`/stats` - サーバー / Bot 統計情報\n"
                "`/about` - Botの情報"
            ),
            inline=False
        )

        # ------------------------------
        # 管理コマンド（権限ありのみ）
        # ------------------------------
        if is_moderator:
            embed.add_field(
                name="🛡 管理コマンド",
                value=(
                    "`/ban` - ユーザーをBAN\n"
                    "`/timeout` - タイムアウト\n"
                    "`/unban` - BAN解除\n"
                    "`/untimeout` - タイムアウト解除"
                ),
                inline=False
            )

            embed.set_footer(text="🔒 管理者権限を検出しました")

        else:
            embed.set_footer(
                text="※ 管理コマンドは権限を持つユーザーのみ表示されます"
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
