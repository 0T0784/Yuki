# ==========================================
# about.py
# ABOUTコマンド
#
# ・Botの基本情報を表示
# ・バージョン / 稼働環境の確認用
# ==========================================

import discord
from discord import app_commands
from discord.ext import commands
import platform


class About(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="about",
        description="Botの情報を表示します"
    )
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Bot情報",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Bot名",
            value=self.bot.user.name,
            inline=False
        )

        embed.add_field(
            name="Python",
            value=platform.python_version(),
            inline=True
        )

        embed.add_field(
            name="discord.py",
            value=discord.__version__,
            inline=True
        )

        embed.add_field(
            name="導入サーバー数",
            value=f"{len(self.bot.guilds)}",
            inline=False
        )

        embed.set_footer(text="Made with discord.py")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(About(bot))
