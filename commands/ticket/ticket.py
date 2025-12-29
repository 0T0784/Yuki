"""
/ticket コマンド
デバッグ用チケット管理コマンド
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Ticket(commands.Cog):
    """
    チケット管理コマンドのCog
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
    
    @app_commands.command(name="ticket", description="チケット管理(デバッグ用)")
    @app_commands.describe(
        operation="操作を選択してください",
        creator="チケット作成者(作成時のみ)"
    )
    @app_commands.choices(operation=[
        app_commands.Choice(name="作成", value="add"),
        app_commands.Choice(name="クローズ", value="close"),
        app_commands.Choice(name="削除", value="del")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket(
        self,
        interaction: discord.Interaction,
        operation: app_commands.Choice[str],
        creator: discord.Member = None
    ):
        """
        チケット管理コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            operation: 操作(add/close/del)
            creator: チケット作成者
        """
        if operation.value == "add":
            # チケット作成
            if not creator:
                await interaction.response.send_message(
                    "❌ チケット作成者を指定してください。",
                    ephemeral=True
                )
                return
            
            # 既にチケットを持っているかチェック
            existing_tickets = []
            for channel in interaction.guild.text_channels:
                if channel.name.startswith(f"ticket-{creator.name.lower()}"):
                    existing_tickets.append(channel)
            
            if existing_tickets:
                await interaction.response.send_message(
                    f"❌ {creator.mention}は既にチケットを持っています: {existing_tickets[0].mention}",
                    ephemeral=True
                )
                return
            
            try:
                # チケットカテゴリを取得または作成
                category = discord.utils.get(interaction.guild.categories, name="Tickets")
                if not category:
                    category = await interaction.guild.create_category("Tickets")
                
                # チケットチャンネルの作成
                channel_name = f"ticket-{creator.name.lower()}-{creator.discriminator}"
                
                # 権限設定
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    creator: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        attach_files=True,
                        embed_links=True
                    ),
                    interaction.guild.me: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_channels=True
                    )
                }
                
                # 管理者ロールに権限を追加
                for role in interaction.guild.roles:
                    if role.permissions.administrator:
                        overwrites[role] = discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True,
                            manage_channels=True
                        )
                
                # チャンネルを作成
                ticket_channel = await interaction.guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    topic=f"チケット作成者: {creator.name}"
                )
                
                # データベースに記録
                cursor = await self.db.connection.execute('''
                    INSERT INTO tickets (guild_id, channel_id, creator_id, status)
                    VALUES (?, ?, ?, ?)
                ''', (interaction.guild_id, ticket_channel.id, creator.id, 'open'))
                
                ticket_id = cursor.lastrowid
                await self.db.connection.commit()
                
                # チケットチャンネルにウェルカムメッセージを送信
                welcome_embed = discord.Embed(
                    title=f"🎫 チケット #{ticket_id}",
                    description=f"管理者によって作成されたチケットです。\n作成者: {creator.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                await ticket_channel.send(embed=welcome_embed)
                
                # 成功メッセージ
                await interaction.response.send_message(
                    f"✅ {creator.mention}のチケットを作成しました: {ticket_channel.mention}",
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name}が{creator.name}のチケット#{ticket_id}を作成しました')
            
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ チケット作成中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'チケット作成エラー: {e}')
        
        elif operation.value == "close":
            # チケットクローズ
            # 現在のチャンネルがチケットチャンネルかチェック
            if not interaction.channel.name.startswith("ticket-"):
                await interaction.response.send_message(
                    "❌ このコマンドはチケットチャンネル内でのみ使用できます。",
                    ephemeral=True
                )
                return
            
            try:
                # データベースからチケット情報を取得
                cursor = await self.db.connection.execute('''
                    SELECT ticket_id, creator_id, status FROM tickets
                    WHERE channel_id = ? AND guild_id = ?
                ''', (interaction.channel.id, interaction.guild_id))
                
                row = await cursor.fetchone()
                
                if not row:
                    await interaction.response.send_message(
                        "❌ このチケットの情報が見つかりません。",
                        ephemeral=True
                    )
                    return
                
                ticket_id, creator_id, status = row
                
                if status == 'closed':
                    await interaction.response.send_message(
                        "❌ このチケットは既にクローズされています。",
                        ephemeral=True
                    )
                    return
                
                # チケットをクローズ
                await self.db.connection.execute('''
                    UPDATE tickets
                    SET status = 'closed', closed_at = ?
                    WHERE ticket_id = ?
                ''', (datetime.now(), ticket_id))
                
                await self.db.connection.commit()
                
                # クローズメッセージ
                close_embed = discord.Embed(
                    title="🔒 チケットクローズ",
                    description=f"このチケットは{interaction.user.mention}によってクローズされました。\n"
                               f"このチャンネルは1週間後に自動的に削除されます。",
                    color=discord.Color.greyple(),
                    timestamp=datetime.now()
                )
                
                await interaction.channel.send(embed=close_embed)
                await interaction.response.send_message("✅ チケットをクローズしました。", ephemeral=True)
                
                logger.info(f'{interaction.user.name}がチケット#{ticket_id}をクローズしました')
            
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ チケットクローズ中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'チケットクローズエラー: {e}')
        
        else:  # delete
            # チケット削除
            if not interaction.channel.name.startswith("ticket-"):
                await interaction.response.send_message(
                    "❌ このコマンドはチケットチャンネル内でのみ使用できます。",
                    ephemeral=True
                )
                return
            
            try:
                # データベースから削除
                await self.db.connection.execute('''
                    DELETE FROM tickets
                    WHERE channel_id = ? AND guild_id = ?
                ''', (interaction.channel.id, interaction.guild_id))
                
                await self.db.connection.commit()
                
                # チャンネルを削除
                await interaction.response.send_message("✅ このチケットを削除します...", ephemeral=True)
                await interaction.channel.delete(reason=f"実行者: {interaction.user.name}")
                
                logger.info(f'{interaction.user.name}がチケットチャンネルを削除しました')
            
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ チケット削除中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'チケット削除エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Ticket(bot))