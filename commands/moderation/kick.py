"""
/kick コマンド
ユーザーをサーバーからキック
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Kick(commands.Cog):
    """キックコマンドのCog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    async def cog_load(self):
        await self.db.initialize()
    
    @app_commands.command(name="kick", description="指定したユーザーをキックします")
    @app_commands.describe(
        user="キックするユーザー",
        reason="キックの理由",
        other_reason="理由が「その他」の場合の詳細"
    )
    @app_commands.choices(reason=[
        app_commands.Choice(name="スパム行為", value="spam"),
        app_commands.Choice(name="不適切な発言", value="inappropriate"),
        app_commands.Choice(name="ルール違反", value="rule_violation"),
        app_commands.Choice(name="荒らし行為", value="trolling"),
        app_commands.Choice(name="その他", value="other")
    ])
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
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
                "❌ 自分自身をキックすることはできません。",
                ephemeral=True
            )
            return
        
        if user.bot:
            await interaction.response.send_message(
                "❌ Botをキックすることはできません。",
                ephemeral=True
            )
            return
        
        if user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ 管理者をキックすることはできません。",
                ephemeral=True
            )
            return
        
        reason_text = reason.name if reason.value != "other" else other_reason
        
        try:
            await user.kick(reason=reason_text)
            
            # モデレーションログ
            await self.db.connection.execute('''
                INSERT INTO moderation_logs
                (guild_id, moderator_id, target_id, action_type, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                interaction.guild_id,
                interaction.user.id,
                user.id,
                'kick',
                reason_text
            ))
            await self.db.connection.commit()
            
            embed = discord.Embed(
                title="👢 キック実行",
                description=f"{user.mention}をキックしました。",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(name="対象ユーザー", value=user.mention, inline=True)
            embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
            embed.add_field(name="理由", value=reason_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            try:
                dm_embed = discord.Embed(
                    title="👢 キック通知",
                    description=f"{interaction.guild.name}でキックされました。",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                dm_embed.add_field(name="理由", value=reason_text, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                logger.warning(f'{user.name}へのDM送信に失敗しました(キック通知)')
            
            logger.info(f'{interaction.user.name}が{user.name}をキックしました (理由: {reason_text})')
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ キックの権限がありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ キック中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'キックエラー: {e}')


async def setup(bot):
    await bot.add_cog(Kick(bot))
