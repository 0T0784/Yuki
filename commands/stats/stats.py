"""
/stats コマンド
サーバーの統計を表示します
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Stats(commands.Cog):
    """
    統計表示コマンドのCog
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
    
    @app_commands.command(name="stats", description="サーバーの統計を表示します")
    @app_commands.describe(period="期間を選択してください")
    @app_commands.choices(period=[
        app_commands.Choice(name="週次統計", value="week"),
        app_commands.Choice(name="月次統計", value="month")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def stats(
        self,
        interaction: discord.Interaction,
        period: app_commands.Choice[str]
    ):
        """
        統計表示コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            period: 期間(week/month)
        """
        # 期間の計算
        now = datetime.now()
        if period.value == "week":
            start_date = now - timedelta(days=7)
            period_text = "週次"
        else:
            start_date = now - timedelta(days=30)
            period_text = "月次"
        
        try:
            guild = interaction.guild
            
            # 総メッセージ数を取得
            cursor = await self.db.connection.execute('''
                SELECT SUM(message_count) FROM user_stats
                WHERE guild_id = ? AND last_updated >= ?
            ''', (guild.id, start_date))
            
            row = await cursor.fetchone()
            total_messages = row[0] if row[0] else 0
            
            # アクティブユーザー数(メッセージを送信したユーザー)
            cursor = await self.db.connection.execute('''
                SELECT COUNT(DISTINCT user_id) FROM user_stats
                WHERE guild_id = ? AND last_updated >= ? AND message_count > 0
            ''', (guild.id, start_date))
            
            row = await cursor.fetchone()
            active_users = row[0] if row[0] else 0
            
            # トップ5アクティブユーザー
            cursor = await self.db.connection.execute('''
                SELECT user_id, message_count FROM user_stats
                WHERE guild_id = ? AND last_updated >= ?
                ORDER BY message_count DESC
                LIMIT 5
            ''', (guild.id, start_date))
            
            top_users = await cursor.fetchall()
            
            # モデレーションアクション数
            cursor = await self.db.connection.execute('''
                SELECT action_type, COUNT(*) FROM moderation_logs
                WHERE guild_id = ? AND created_at >= ?
                GROUP BY action_type
            ''', (guild.id, start_date))
            
            moderation_actions = await cursor.fetchall()
            
            # チケット数
            cursor = await self.db.connection.execute('''
                SELECT COUNT(*) FROM tickets
                WHERE guild_id = ? AND created_at >= ?
            ''', (guild.id, start_date))
            
            row = await cursor.fetchone()
            ticket_count = row[0] if row[0] else 0
            
            # Embedの作成
            embed = discord.Embed(
                title=f"📊 {guild.name}の{period_text}統計",
                description=f"{start_date.strftime('%Y/%m/%d')} から {now.strftime('%Y/%m/%d')} までの統計",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            # 基本統計
            embed.add_field(
                name="💬 総メッセージ数",
                value=f"{total_messages:,}件",
                inline=True
            )
            
            embed.add_field(
                name="👥 アクティブユーザー",
                value=f"{active_users}人",
                inline=True
            )
            
            embed.add_field(
                name="🎫 チケット作成数",
                value=f"{ticket_count}件",
                inline=True
            )
            
            # トップ5アクティブユーザー
            if top_users:
                top_users_text = ""
                for i, (user_id, msg_count) in enumerate(top_users, 1):
                    member = guild.get_member(user_id)
                    if member:
                        top_users_text += f"{i}. {member.mention}: {msg_count:,}件\n"
                
                if top_users_text:
                    embed.add_field(
                        name="🏆 トップアクティブユーザー",
                        value=top_users_text,
                        inline=False
                    )
            
            # モデレーションアクション
            if moderation_actions:
                action_text = ""
                action_icons = {
                    'timeout': '⏱️',
                    'untimeout': '✅',
                    'kick': '🥾',
                    'ban': '🔨'
                }
                for action_type, count in moderation_actions:
                    icon = action_icons.get(action_type, '🛡️')
                    action_text += f"{icon} {action_type}: {count}件\n"
                
                embed.add_field(
                    name="🛡️ モデレーションアクション",
                    value=action_text,
                    inline=False
                )
            
            # サーバー情報
            embed.add_field(
                name="📈 現在のメンバー数",
                value=f"{guild.member_count}人",
                inline=True
            )
            
            embed.add_field(
                name="📅 集計期間",
                value=f"{period_text}({7 if period.value == 'week' else 30}日間)",
                inline=True
            )
            
            embed.set_footer(text=f"実行者: {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f'{interaction.user.name}が{period_text}統計を表示しました')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 統計取得中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'統計取得エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Stats(bot))
