# ==========================================
# ping.py
# PINGコマンド（一般向け）
#
# ・Botの応答速度を測定
# ・Discord WebSocketのレイテンシ表示
# ・Botの生存確認・通信状態確認用
# ==========================================

import time
import discord
from discord import app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Botの応答速度を表示します"
    )
    async def ping(self, interaction: discord.Interaction):
        # ------------------------------
        # 計測開始時間
        # ------------------------------
        start_time = time.perf_counter()

        # ------------------------------
        # 仮レスポンス（先に返す）
        # ------------------------------
        await interaction.response.send_message(
            "🏓 Ping計測中...",
            ephemeral=True
        )

        # ------------------------------
        # 応答時間計算（ms）
        # ------------------------------
        response_ms = (time.perf_counter() - start_time) * 1000

        # ------------------------------
        # WebSocketレイテンシ（ms）
        # ------------------------------
        ws_latency = self.bot.latency * 1000

        # ------------------------------
        # Embed生成
        # ------------------------------
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📡 応答速度",
            value=f"{response_ms:.2f} ms",
            inline=False
        )

        embed.add_field(
            name="🌐 WebSocketレイテンシ",
            value=f"{ws_latency:.2f} ms",
            inline=False
        )

        # ------------------------------
        # 結果表示
        # ------------------------------
        await interaction.edit_original_response(
            content=None,
            embed=embed
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
