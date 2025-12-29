"""
/logs コマンド
ログチャンネルの設定を行います
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Logs(commands.Cog):
    """
    ログ設定コマンドのCog
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
    
    @app_commands.command(name="logs", description="ログチャンネルの設定を行います")
    @app_commands.describe(
        channel="ログチャンネルを選択してください",
        log_type="ログタイプを選択してください"
    )
    @app_commands.choices(log_type=[
        app_commands.Choice(name="公開ログ", value="public"),
        app_commands.Choice(name="管理ログ", value="private"),
        app_commands.Choice(name="レポートログ", value="report"),
        app_commands.Choice(name="デバッグ(テスト送信)", value="debug")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        log_type: app_commands.Choice[str]
    ):
        """
        ログ設定コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            channel: ログチャンネル
            log_type: ログタイプ
        """
        if log_type.value == "debug":
            # デバッグモード: テストログを送信
            try:
                # 各種ログのサンプルを送信
                
                # 公開ログのサンプル
                public_embed = discord.Embed(
                    title="📢 公開ログ (テスト)",
                    description="これは公開ログのテストメッセージです。\n"
                               "すべてのメンバーが閲覧可能なログがここに記録されます。",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                public_embed.add_field(
                    name="例",
                    value="• メンバーの参加/退出\n• チャンネルの作成/削除\n• ロールの変更",
                    inline=False
                )
                await channel.send(embed=public_embed)
                
                # 管理ログのサンプル
                private_embed = discord.Embed(
                    title="🔒 管理ログ (テスト)",
                    description="これは管理ログのテストメッセージです。\n"
                               "管理者のみが閲覧可能なログがここに記録されます。",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                private_embed.add_field(
                    name="例",
                    value="• モデレーションアクション\n• 権限の変更\n• 設定の変更",
                    inline=False
                )
                await channel.send(embed=private_embed)
                
                # レポートログのサンプル
                report_embed = discord.Embed(
                    title="📝 レポートログ (テスト)",
                    description="これはレポートログのテストメッセージです。\n"
                               "ユーザーからのレポートがここに記録されます。",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                report_embed.add_field(
                    name="例",
                    value="• ユーザーの不適切な行動の報告\n• Botのバグ報告",
                    inline=False
                )
                await channel.send(embed=report_embed)
                
                # 成功メッセージ
                await interaction.response.send_message(
                    f"✅ {channel.mention}にテストログを送信しました。",
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name}がテストログを送信しました')
            
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"❌ {channel.mention}にメッセージを送信する権限がありません。",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ テストログ送信中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'テストログ送信エラー: {e}')
        
        else:
            # 通常モード: ログチャンネルを設定
            try:
                # データベースのカラム名を決定
                column_map = {
                    'public': 'public_log_channel_id',
                    'private': 'private_log_channel_id',
                    'report': 'report_log_channel_id'
                }
                
                column = column_map[log_type.value]
                
                # データベースに保存
                await self.db.connection.execute(f'''
                    INSERT INTO guild_settings (guild_id, {column})
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET
                        {column} = ?
                ''', (interaction.guild_id, channel.id, channel.id))
                
                await self.db.connection.commit()
                
                # 成功メッセージ
                log_type_names = {
                    'public': '公開ログ',
                    'private': '管理ログ',
                    'report': 'レポートログ'
                }
                
                embed = discord.Embed(
                    title="✅ ログチャンネルを設定しました",
                    description=f"{log_type_names[log_type.value]}チャンネルを設定しました。",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="ログタイプ", value=log_type_names[log_type.value], inline=True)
                embed.add_field(name="チャンネル", value=channel.mention, inline=True)
                embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
                
                await interaction.response.send_message(embed=embed)
                
                # 設定完了通知をログチャンネルに送信
                notification_embed = discord.Embed(
                    title="🔔 ログチャンネル設定完了",
                    description=f"このチャンネルが{log_type_names[log_type.value]}チャンネルとして設定されました。",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                notification_embed.add_field(
                    name="設定者",
                    value=interaction.user.mention,
                    inline=True
                )
                
                await channel.send(embed=notification_embed)
                
                logger.info(
                    f'{interaction.user.name}が{log_type.value}ログチャンネルを設定しました '
                    f'(チャンネル: {channel.name})'
                )
            
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ ログチャンネル設定中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'ログチャンネル設定エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Logs(bot))
