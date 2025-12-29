"""
/ban コマンド
ユーザーをサーバーからBAN
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Ban(commands.Cog):
    """バンコマンドのCog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    async def cog_load(self):
        await self.db.initialize()
    
    @app_commands.command(name="ban", description="指定したユーザーをBANします")
    @app_commands.describe(
        user="BANするユーザー",
        reason="BANの理由",
        other_reason="理由が「その他」の場合の詳細"
    )
    @app_commands.choices(reason=[
        app_commands.Choice(name="スパム行為", value="spam"),
        app_commands.Choice(name="不適切な発言", value="inappropriate"),
        app_commands.Choice(name="ルール違反", value="rule_violation"),
        app_commands.Choice(name="荒らし行為", value="trolling"),
        app_commands.Choice(name="その他", value="other")
    ])
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: app_commands.Choice[str],
        other_reason: str = None
    ):
        if reason.value == "other" and not other_reason:
            await interaction.response.send_message(
                "❌ 理由に「その他」を選択した場合は、詳細を記述してください。",
                ephemeral=True
            )
            return
        
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ 自分自身をBANすることはできません。",
                ephemeral=True
            )
            return
        
        if user.bot:
            await interaction.response.send_message(
                "❌ BotをBANすることはできません。",
                ephemeral=True
            )
            return
        
        if user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ 管理者をBANすることはできません。",
                ephemeral=True
            )
            return
        
        reason_text = reason.name if reason.value != "other" else other_reason
        
        try:
            await user.ban(reason=reason_text)
            
            # モデレーションログ
            await self.db.connection.execute('''
                INSERT INTO moderation_logs
                (guild_id, moderator_id, target_id, action_type, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                interaction.guild_id,
                interaction.user.id,
                user.id,
                'ban',
                reason_text
            ))
            await self.db.connection.commit()
            
            embed = discord.Embed(
                title="🔨 BAN実行",
                description=f"{user.mention}をBANしました。",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="対象ユーザー", value=user.mention, inline=True)
            embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
            embed.add_field(name="理由", value=reason_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            try:
                dm_embed = discord.Embed(
                    title="🔨 BAN通知",
                    description=f"{interaction.guild.name}でBANされました。",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                dm_embed.add_field(name="理由", value=reason_text, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                logger.warning(f'{user.name}へのDM送信に失敗しました(BAN通知)')
            
            logger.info(f'{interaction.user.name}が{user.name}をBANしました (理由: {reason_text})')
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ BANの権限がありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ BAN中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'BANエラー: {e}')
    
    @app_commands.command(name="unban", description="BANを解除します")
    @app_commands.describe(
        user_id="解除するユーザーのID",
        reason="解除理由",
        other_reason="理由が「その他」の場合の詳細"
    )
    @app_commands.choices(reason=[
        app_commands.Choice(name="誤BAN", value="mistake"),
        app_commands.Choice(name="反省が見られた", value="reformed"),
        app_commands.Choice(name="期間短縮", value="reduced"),
        app_commands.Choice(name="その他", value="other")
    ])
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: int,
        reason: app_commands.Choice[str],
        other_reason: str = None
    ):
        if reason.value == "other" and not other_reason:
            await interaction.response.send_message(
                "❌ 理由に「その他」を選択した場合は、詳細を記述してください。",
                ephemeral=True
            )
            return
        
        reason_text = reason.name if reason.value != "other" else other_reason
        
        try:
            banned_users = await interaction.guild.bans()
            user = discord.utils.get(banned_users, user__id=user_id)
            if not user:
                await interaction.response.send_message(
                    "❌ 指定されたユーザーはBANされていません。",
                    ephemeral=True
                )
                return
            
            await interaction.guild.unban(user.user, reason=reason_text)
            
            await self.db.connection.execute('''
                INSERT INTO moderation_logs
                (guild_id, moderator_id, target_id, action_type, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                interaction.guild_id,
                interaction.user.id,
                user.user.id,
                'unban',
                reason_text
            ))
            await self.db.connection.commit()
            
            embed = discord.Embed(
                title="✅ BAN解除",
                description=f"{user.user.mention}のBANを解除しました。",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="対象ユーザー", value=user.user.mention, inline=True)
            embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
            embed.add_field(name="理由", value=reason_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            try:
                dm_embed = discord.Embed(
                    title="✅ BAN解除通知",
                    description=f"{interaction.guild.name}でBANが解除されました。",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                dm_embed.add_field(name="理由", value=reason_text, inline=False)
                await user.user.send(embed=dm_embed)
            except discord.Forbidden:
                logger.warning(f'{user.user.name}へのDM送信に失敗しました(BAN解除通知)')
            
            logger.info(f'{interaction.user.name}が{user.user.name}のBANを解除しました (理由: {reason_text})')
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ BAN解除の権限がありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ BAN解除中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'BAN解除エラー: {e}')


async def setup(bot):
    await bot.add_cog(Ban(bot))
