"""
/info コマンド
Bot、管理者、ユーザー、サーバーの情報を表示します
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Info(commands.Cog):
    """
    情報表示コマンドのCog
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
        self.db = Database()
    
    async def cog_load(self):
        """
        Cog読み込み時の処理
        """
        await self.db.initialize()
    
    @app_commands.command(name="info", description="Bot、管理者、ユーザー、サーバーの情報を表示します")
    @app_commands.describe(
        type="情報のタイプを選択してください",
        user="ユーザー情報を表示する場合、対象ユーザーを指定してください"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Bot情報", value="bot"),
        app_commands.Choice(name="管理者情報", value="admin"),
        app_commands.Choice(name="ユーザー情報", value="user"),
        app_commands.Choice(name="サーバー情報", value="server")
    ])
    async def info(
        self,
        interaction: discord.Interaction,
        type: app_commands.Choice[str],
        user: discord.Member = None
    ):
        """
        情報表示コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            type: 情報タイプ
            user: 対象ユーザー(オプション)
        """
        # タイプに応じて処理を分岐
        if type.value == "bot":
            await self._show_bot_info(interaction)
        elif type.value == "admin":
            await self._show_admin_info(interaction)
        elif type.value == "user":
            await self._show_user_info(interaction, user)
        elif type.value == "server":
            await self._show_server_info(interaction)
    
    async def _show_bot_info(self, interaction: discord.Interaction):
        """
        Bot情報を表示
        
        Args:
            interaction: インタラクション
        """
        embed = discord.Embed(
            title="🤖 Bot情報",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Botのアイコン設定
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Bot名
        embed.add_field(
            name="Bot名",
            value=self.bot.user.name,
            inline=True
        )
        
        # バージョン
        version = os.getenv('BOT_VERSION', '1.0.0')
        embed.add_field(
            name="バージョン",
            value=version,
            inline=True
        )
        
        # 作成者
        author = os.getenv('BOT_AUTHOR', '未設定')
        embed.add_field(
            name="作成者",
            value=author,
            inline=True
        )
        
        # 参加サーバー数
        embed.add_field(
            name="参加サーバー数",
            value=f"{len(self.bot.guilds)}サーバー",
            inline=True
        )
        
        # 総ユーザー数
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(
            name="総ユーザー数",
            value=f"{total_users}人",
            inline=True
        )
        
        # Ping
        embed.add_field(
            name="応答速度",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user.name}がBot情報を表示しました')
    
    async def _show_admin_info(self, interaction: discord.Interaction):
        """
        管理者情報を表示
        
        Args:
            interaction: インタラクション
        """
        guild = interaction.guild
        
        # オーナー数(1人)
        owner_count = 1
        
        # 管理者権限を持つメンバー数
        admin_count = sum(
            1 for member in guild.members
            if member.guild_permissions.administrator and not member.bot
        )
        
        # Botロールを持つメンバー数
        bot_count = sum(1 for member in guild.members if member.bot)
        
        embed = discord.Embed(
            title="👑 管理者情報",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="サーバーオーナー",
            value=f"{guild.owner.mention}\n({guild.owner.name})",
            inline=False
        )
        
        embed.add_field(
            name="管理者数",
            value=f"{admin_count}人",
            inline=True
        )
        
        embed.add_field(
            name="Bot数",
            value=f"{bot_count}個",
            inline=True
        )
        
        embed.set_footer(text=f"サーバー: {guild.name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user.name}が管理者情報を表示しました')
    
    async def _show_user_info(self, interaction: discord.Interaction, user: discord.Member):
        """
        ユーザー情報を表示
        
        Args:
            interaction: インタラクション
            user: 対象ユーザー
        """
        # ユーザーが指定されていない場合は自分自身
        if user is None:
            user = interaction.user
        else:
            # 管理者権限チェック
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ 他のユーザーの情報を表示するには管理者権限が必要です。",
                    ephemeral=True
                )
                return
        
        # データベースから統計情報を取得
        stats = await self.db.get_user_stats(interaction.guild_id, user.id)
        
        embed = discord.Embed(
            title=f"👤 {user.name}のユーザー情報",
            color=user.color,
            timestamp=datetime.now()
        )
        
        # ユーザーアイコン
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        # 基本情報
        embed.add_field(
            name="ユーザー名",
            value=user.mention,
            inline=True
        )
        
        embed.add_field(
            name="アカウント作成日",
            value=user.created_at.strftime('%Y/%m/%d'),
            inline=True
        )
        
        embed.add_field(
            name="サーバー参加日",
            value=user.joined_at.strftime('%Y/%m/%d') if user.joined_at else "不明",
            inline=True
        )
        
        # 統計情報
        embed.add_field(
            name="📊 発言数",
            value=f"{stats['message_count']}回",
            inline=True
        )
        
        # 管理者の場合は詳細情報も表示
        if interaction.user.guild_permissions.administrator:
            embed.add_field(
                name="⏱️ タイムアウト回数",
                value=f"{stats['timeout_count']}回",
                inline=True
            )
            
            embed.add_field(
                name="🥾 キック回数",
                value=f"{stats['kick_count']}回",
                inline=True
            )
            
            embed.add_field(
                name="🔨 BAN回数",
                value=f"{stats['ban_count']}回",
                inline=True
            )
            
            embed.add_field(
                name="🎫 チケット作成数",
                value=f"{stats['ticket_count']}回",
                inline=True
            )
        
        embed.set_footer(text=f"User ID: {user.id}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user.name}が{user.name}のユーザー情報を表示しました')
    
    async def _show_server_info(self, interaction: discord.Interaction):
        """
        サーバー情報を表示
        
        Args:
            interaction: インタラクション
        """
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}のサーバー情報",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # サーバーアイコン
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # 基本情報
        embed.add_field(
            name="サーバーオーナー",
            value=guild.owner.mention,
            inline=True
        )
        
        embed.add_field(
            name="作成日",
            value=guild.created_at.strftime('%Y/%m/%d'),
            inline=True
        )
        
        embed.add_field(
            name="メンバー数",
            value=f"{guild.member_count}人",
            inline=True
        )
        
        # チャンネル情報
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="テキストチャンネル",
            value=f"{text_channels}個",
            inline=True
        )
        
        embed.add_field(
            name="ボイスチャンネル",
            value=f"{voice_channels}個",
            inline=True
        )
        
        embed.add_field(
            name="カテゴリ",
            value=f"{categories}個",
            inline=True
        )
        
        # ロール数
        embed.add_field(
            name="ロール数",
            value=f"{len(guild.roles)}個",
            inline=True
        )
        
        # 絵文字数
        embed.add_field(
            name="絵文字数",
            value=f"{len(guild.emojis)}個",
            inline=True
        )
        
        # ブースト情報
        embed.add_field(
            name="ブーストレベル",
            value=f"レベル {guild.premium_tier}",
            inline=True
        )
        
        embed.set_footer(text=f"Server ID: {guild.id}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user.name}がサーバー情報を表示しました')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Info(bot))
