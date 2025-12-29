"""
/ping コマンド
Botの応答速度を表示します
"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import get_logger

logger = get_logger()


class Ping(commands.Cog):
    """
    Pingコマンドのcog
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
    
    @app_commands.command(name="ping", description="Botの応答速度を表示します")
    async def ping(self, interaction: discord.Interaction):
        """
        Pingコマンドのメイン処理
        
        Args:
            interaction: インタラクション
        """
        # WebSocket接続のレイテンシを取得(ミリ秒に変換)
        latency = round(self.bot.latency * 1000)
        
        # レイテンシに応じて色を変更
        if latency < 100:
            color = discord.Color.green()
            status = "🟢 良好"
        elif latency < 200:
            color = discord.Color.yellow()
            status = "🟡 普通"
        else:
            color = discord.Color.red()
            status = "🔴 遅延"
        
        # Embedの作成
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Botの応答速度を測定しました。",
            color=color
        )
        
        embed.add_field(
            name="WebSocketレイテンシ",
            value=f"{latency}ms",
            inline=True
        )
        
        embed.add_field(
            name="ステータス",
            value=status,
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user.name}がPingコマンドを使用しました (レイテンシ: {latency}ms)')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Ping(bot))
