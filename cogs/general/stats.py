# ==========================================
# stats.py
# サーバー統計 & 治安状況の可視化
# ==========================================

import discord
from discord.ext import commands
from discord import app_commands
from database.db import fetch_mod_stats


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="stats",
        description="サーバーの治安状況と処罰統計を表示します"
    )
    async def stats(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        # DBから統計を取得
        stats = fetch_mod_stats(guild_id)

        ban = stats.get("BAN", 0)
        unban = stats.get("UNBAN", 0)
        timeout = stats.get("TIMEOUT", 0)
        untimeout = stats.get("UNTIMEOUT", 0)
        kick = stats.get("KICK", 0)

        total = ban + timeout + kick

        # 治安スコア計算
        score = (
            ban * 5 +
            timeout * 2 +
            kick * 1 -
            unban * 5 -
            untimeout * 2
        )

        # 治安ランク判定
        if score <= 5:
            level = "🟢 非常に良好"
        elif score <= 15:
            level = "🟡 やや不安"
        elif score <= 30:
            level = "🟠 注意"
        else:
            level = "🔴 危険"

        embed = discord.Embed(
            title="📊 サーバー治安レポート",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🚨 処罰統計",
            value=(
                f"BAN: {ban}\n"
                f"UNBAN: {unban}\n"
                f"TIMEOUT: {timeout}\n"
                f"UNTIMEOUT: {untimeout}\n"
                f"KICK: {kick}\n"
                f"合計処罰数: {total}"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡 治安レベル",
            value=f"{level}\n(スコア: {score})",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
