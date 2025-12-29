"""
/timeout, /untimeout コマンド
ユーザーのタイムアウト処理を行います
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta, datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Timeout(commands.Cog):
    """
    タイムアウトコマンドのCog
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
    
    @app_commands.command(name="timeout", description="指定したユーザーをタイムアウトします")
    @app_commands.describe(
        user="タイムアウトするユーザー",
        reason="タイムアウトの理由",
        minutes="タイムアウトの時間(分)",
        other_reason="理由が「その他」の場合の詳細"
    )
    @app_commands.choices(reason=[
        app_commands.Choice(name="スパム行為", value="spam"),
        app_commands.Choice(name="不適切な発言", value="inappropriate"),
        app_commands.Choice(name="ルール違反", value="rule_violation"),
        app_commands.Choice(name="荒らし行為", value="trolling"),
        app_commands.Choice(name="その他", value="other")
    ])
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: app_commands.Choice[str],
        minutes: int,
        other_reason: str = None
    ):
        """
        タイムアウトコマンドのメイン処理
        
        Args:
            interaction: インタラクション
            user: 対象ユーザー
            reason: タイムアウト理由
            minutes: タイムアウト時間(分)
            other_reason: その他の理由の詳細
        """
        # 理由が「その他」の場合、詳細が必須
        if reason.value == "other" and not other_reason:
            await interaction.response.send_message(
                "❌ 理由に「その他」を選択した場合は、詳細を記述してください。",
                ephemeral=True
            )
            return
        
        # 自分自身をタイムアウトできないようにチェック
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ 自分自身をタイムアウトすることはできません。",
                ephemeral=True
            )
            return
        
        # Botをタイムアウトできないようにチェック
        if user.bot:
            await interaction.response.send_message(
                "❌ Botをタイムアウトすることはできません。",
                ephemeral=True
            )
            return
        
        # 管理者をタイムアウトできないようにチェック
        if user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ 管理者をタイムアウトすることはできません。",
                ephemeral=True
            )
            return
        
        # タイムアウト時間が有効かチェック(1分〜40320分=28日)
        if minutes < 1 or minutes > 40320:
            await interaction.response.send_message(
                "❌ タイムアウト時間は1分から40320分(28日)の間で指定してください。",
                ephemeral=True
            )
            return
        
        # 理由のテキストを取得
        reason_text = reason.name if reason.value != "other" else other_reason
        
        try:
            # タイムアウトの実行
            duration = timedelta(minutes=minutes)
            await user.timeout(duration, reason=reason_text)
            
            # データベースに記録
            await self.db.connection.execute('''
                INSERT INTO user_stats (guild_id, user_id, timeout_count, last_updated)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    timeout_count = timeout_count + 1,
                    last_updated = ?
            ''', (interaction.guild_id, user.id, datetime.now(), datetime.now()))
            
            # モデレーションログに記録
            await self.db.connection.execute('''
                INSERT INTO moderation_logs
                (guild_id, moderator_id, target_id, action_type, reason, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                interaction.guild_id,
                interaction.user.id,
                user.id,
                'timeout',
                reason_text,
                minutes
            ))
            
            await self.db.connection.commit()
            
            # 成功メッセージ
            embed = discord.Embed(
                title="⏱️ タイムアウト実行",
                description=f"{user.mention}をタイムアウトしました。",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="対象ユーザー", value=user.mention, inline=True)
            embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
            embed.add_field(name="時間", value=f"{minutes}分", inline=True)
            embed.add_field(name="理由", value=reason_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            # 対象ユーザーにDM送信
            try:
                dm_embed = discord.Embed(
                    title="⏱️ タイムアウト通知",
                    description=f"{interaction.guild.name}でタイムアウトされました。",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                dm_embed.add_field(name="時間", value=f"{minutes}分", inline=True)
                dm_embed.add_field(name="理由", value=reason_text, inline=False)
                dm_embed.add_field(
                    name="タイムアウト終了時刻",
                    value=f"<t:{int((datetime.now() + duration).timestamp())}:F>",
                    inline=False
                )
                
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                # DMが送信できない場合はログに記録
                logger.warning(f'{user.name}へのDM送信に失敗しました(タイムアウト通知)')
            
            logger.info(
                f'{interaction.user.name}が{user.name}を{minutes}分間タイムアウトしました '
                f'(理由: {reason_text})'
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ タイムアウトの権限がありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ タイムアウト中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'タイムアウトエラー: {e}')
    
    @app_commands.command(name="untimeout", description="タイムアウトを解除します")
    @app_commands.describe(
        user="タイムアウトを解除するユーザー",
        reason="解除の理由",
        other_reason="理由が「その他」の場合の詳細"
    )
    @app_commands.choices(reason=[
        app_commands.Choice(name="誤タイムアウト", value="mistake"),
        app_commands.Choice(name="反省が見られた", value="reformed"),
        app_commands.Choice(name="期間短縮", value="reduced"),
        app_commands.Choice(name="その他", value="other")
    ])
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: app_commands.Choice[str],
        other_reason: str = None
    ):
        """
        タイムアウト解除コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            user: 対象ユーザー
            reason: 解除理由
            other_reason: その他の理由の詳細
        """
        # 理由が「その他」の場合、詳細が必須
        if reason.value == "other" and not other_reason:
            await interaction.response.send_message(
                "❌ 理由に「その他」を選択した場合は、詳細を記述してください。",
                ephemeral=True
            )
            return
        
        # タイムアウトされているかチェック
        if not user.timed_out:
            await interaction.response.send_message(
                "❌ このユーザーはタイムアウトされていません。",
                ephemeral=True
            )
            return
        
        # 理由のテキストを取得
        reason_text = reason.name if reason.value != "other" else other_reason
        
        try:
            # タイムアウトの解除
            await user.timeout(None, reason=reason_text)
            
            # モデレーションログに記録
            await self.db.connection.execute('''
                INSERT INTO moderation_logs
                (guild_id, moderator_id, target_id, action_type, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                interaction.guild_id,
                interaction.user.id,
                user.id,
                'untimeout',
                reason_text
            ))
            
            await self.db.connection.commit()
            
            # 成功メッセージ
            embed = discord.Embed(
                title="✅ タイムアウト解除",
                description=f"{user.mention}のタイムアウトを解除しました。",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="対象ユーザー", value=user.mention, inline=True)
            embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
            embed.add_field(name="理由", value=reason_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            # 対象ユーザーにDM送信
            try:
                dm_embed = discord.Embed(
                    title="✅ タイムアウト解除通知",
                    description=f"{interaction.guild.name}でタイムアウトが解除されました。",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                dm_embed.add_field(name="理由", value=reason_text, inline=False)
                
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                logger.warning(f'{user.name}へのDM送信に失敗しました(タイムアウト解除通知)')
            
            logger.info(
                f'{interaction.user.name}が{user.name}のタイムアウトを解除しました '
                f'(理由: {reason_text})'
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ タイムアウト解除の権限がありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ タイムアウト解除中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'タイムアウト解除エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Timeout(bot))
