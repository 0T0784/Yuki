"""
/stats_send コマンド
統計の定期送信設定を行います
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class StatsSend(commands.Cog):
    """
    統計定期送信コマンドのCog
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
        self.db = Database()
        # 定期送信タスクを開始
        self.send_scheduled_stats.start()
    
    async def cog_load(self):
        """
        Cog読み込み時の処理
        """
        await self.db.initialize()
    
    def cog_unload(self):
        """
        Cogアンロード時の処理
        """
        self.send_scheduled_stats.cancel()
    
    @tasks.loop(hours=1)
    async def send_scheduled_stats(self):
        """
        定期的に統計を送信するタスク
        1時間ごとにチェックして、該当する場合に送信
        """
        now = datetime.now()
        
        try:
            await self.db.initialize()
            
            # 送信すべき統計設定を取得
            cursor = await self.db.connection.execute('''
                SELECT guild_id, channel_id, period, last_sent
                FROM stats_schedule
            ''')
            
            schedules = await cursor.fetchall()
            
            for guild_id, channel_id, period, last_sent in schedules:
                should_send = False
                
                # 最終送信日時をチェック
                last_sent_dt = datetime.fromisoformat(last_sent) if last_sent else None
                
                if period == 'week':
                    # 月曜日の0時〜1時の間
                    if now.weekday() == 0 and now.hour == 0:
                        if not last_sent_dt or (now - last_sent_dt).days >= 7:
                            should_send = True
                
                elif period == 'month':
                    # 毎月1日の0時〜1時の間
                    if now.day == 1 and now.hour == 0:
                        if not last_sent_dt or (now - last_sent_dt).days >= 28:
                            should_send = True
                
                if should_send:
                    # 統計を送信
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            await self._send_stats(guild, channel, period)
                            
                            # 最終送信日時を更新
                            await self.db.connection.execute('''
                                UPDATE stats_schedule
                                SET last_sent = ?
                                WHERE guild_id = ?
                            ''', (now, guild_id))
                            
                            await self.db.connection.commit()
        
        except Exception as e:
            logger.error(f'定期統計送信エラー: {e}')
    
    @send_scheduled_stats.before_loop
    async def before_send_scheduled_stats(self):
        """
        タスク開始前にBotの準備完了を待つ
        """
        await self.bot.wait_until_ready()
    
    async def _send_stats(self, guild: discord.Guild, channel: discord.TextChannel, period: str):
        """
        統計をチャンネルに送信する内部関数
        
        Args:
            guild: サーバー
            channel: 送信先チャンネル
            period: 期間(week/month)
        """
        # 期間の計算
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
            period_text = "週次"
        else:
            start_date = now - timedelta(days=30)
            period_text = "月次"
        
        try:
            # 総メッセージ数を取得
            cursor = await self.db.connection.execute('''
                SELECT SUM(message_count) FROM user_stats
                WHERE guild_id = ? AND last_updated >= ?
            ''', (guild.id, start_date))
            
            row = await cursor.fetchone()
            total_messages = row[0] if row[0] else 0
            
            # アクティブユーザー数
            cursor = await self.db.connection.execute('''
                SELECT COUNT(DISTINCT user_id) FROM user_stats
                WHERE guild_id = ? AND last_updated >= ? AND message_count > 0
            ''', (guild.id, start_date))
            
            row = await cursor.fetchone()
            active_users = row[0] if row[0] else 0
            
            # Embedの作成
            embed = discord.Embed(
                title=f"📊 {period_text}統計レポート",
                description=f"{guild.name}の{period_text}統計をお知らせします。",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
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
                name="📅 集計期間",
                value=f"{start_date.strftime('%Y/%m/%d')} 〜 {now.strftime('%Y/%m/%d')}",
                inline=False
            )
            
            embed.set_footer(text="自動送信")
            
            await channel.send(embed=embed)
            logger.info(f'{guild.name}に{period_text}統計を自動送信しました')
        
        except Exception as e:
            logger.error(f'統計送信エラー: {e}')
    
    @app_commands.command(name="stats_send", description="統計の定期送信設定を行います")
    @app_commands.describe(
        period="送信期間を選択してください",
        channel="送信先チャンネルを選択してください"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="週次(毎週月曜日0:00)", value="week"),
        app_commands.Choice(name="月次(毎月1日0:00)", value="month")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def stats_send(
        self,
        interaction: discord.Interaction,
        period: app_commands.Choice[str],
        channel: discord.TextChannel
    ):
        """
        統計定期送信設定コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            period: 期間(week/month)
            channel: 送信先チャンネル
        """
        try:
            # データベースに設定を保存
            await self.db.connection.execute('''
                INSERT INTO stats_schedule (guild_id, channel_id, period)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_id = ?,
                    period = ?
            ''', (
                interaction.guild_id,
                channel.id,
                period.value,
                channel.id,
                period.value
            ))
            
            await self.db.connection.commit()
            
            # 成功メッセージ
            period_text = "週次(毎週月曜日0:00)" if period.value == "week" else "月次(毎月1日0:00)"
            
            embed = discord.Embed(
                title="✅ 統計定期送信を設定しました",
                description=f"{channel.mention}に{period_text}で統計を送信します。",
                color=discord.Color.green()
            )
            
            embed.add_field(name="送信先", value=channel.mention, inline=True)
            embed.add_field(name="頻度", value=period_text, inline=True)
            embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(
                f'{interaction.user.name}が統計定期送信を設定しました '
                f'(チャンネル: {channel.name}, 期間: {period.value})'
            )
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 設定中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'統計定期送信設定エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(StatsSend(bot))
