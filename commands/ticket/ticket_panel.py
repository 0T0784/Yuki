"""
/ticket_panel コマンド
チケットパネルの作成/削除を行います
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import io
import asyncio
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class TicketCloseButton(View):
    """
    チケットクローズボタンのView
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        super().__init__(timeout=None)
        self.bot = bot
        self.db = Database()
    
    @discord.ui.button(
        label="🔒 チケットをクローズ",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        """
        チケットクローズボタンが押された時の処理
        
        Args:
            interaction: インタラクション
            button: ボタン
        """
        await self.db.initialize()
        
        # 管理者かチケット作成者のみクローズ可能
        cursor = await self.db.connection.execute('''
            SELECT creator_id, status FROM tickets
            WHERE channel_id = ? AND guild_id = ?
        ''', (interaction.channel.id, interaction.guild_id))
        
        row = await cursor.fetchone()
        
        if not row:
            await interaction.response.send_message(
                "❌ このチケットの情報が見つかりません。",
                ephemeral=True
            )
            return
        
        creator_id, status = row
        
        # 権限チェック
        is_admin = interaction.user.guild_permissions.administrator
        is_creator = interaction.user.id == creator_id
        
        if not (is_admin or is_creator):
            await interaction.response.send_message(
                "❌ チケットをクローズできるのは管理者またはチケット作成者のみです。",
                ephemeral=True
            )
            return
        
        if status == 'closed':
            await interaction.response.send_message(
                "❌ このチケットは既にクローズされています。",
                ephemeral=True
            )
            return
        
        try:
            # チケットをクローズ
            await self.db.connection.execute('''
                UPDATE tickets
                SET status = 'closed', closed_at = ?
                WHERE channel_id = ?
            ''', (datetime.now(), interaction.channel.id))
            
            await self.db.connection.commit()
            
            # クローズメッセージとログ生成ボタンを送信
            close_embed = discord.Embed(
                title="🔒 チケットクローズ",
                description=f"このチケットは{interaction.user.mention}によってクローズされました。\n"
                           f"下のボタンからログを生成できます。\n"
                           f"このチャンネルは1週間後に自動的に削除されます。",
                color=discord.Color.greyple(),
                timestamp=datetime.now()
            )
            
            # ログ生成ボタンのViewを作成
            log_view = TicketLogButton(self.bot)
            
            await interaction.response.send_message(embed=close_embed, view=log_view)
            
            logger.info(f'{interaction.user.name}がチケット(チャンネル: {interaction.channel.name})をクローズしました')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ チケットクローズ中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'チケットクローズエラー: {e}')


class TicketLogButton(View):
    """
    チケットログ生成ボタンのView
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(
        label="📄 ログを生成",
        style=discord.ButtonStyle.primary,
        custom_id="generate_log_button"
    )
    async def generate_log(self, interaction: discord.Interaction, button: Button):
        """
        ログ生成ボタンが押された時の処理
        
        Args:
            interaction: インタラクション
            button: ボタン
        """
        # 管理者のみログ生成可能
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ ログを生成できるのは管理者のみです。",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # チャンネルのメッセージ履歴を取得
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                author = f"{message.author.name}#{message.author.discriminator}"
                content = message.content if message.content else "[添付ファイルまたはEmbed]"
                
                messages.append(f"[{timestamp}] {author}: {content}")
            
            # ログファイルを作成
            log_content = "\n".join(messages)
            log_file = io.BytesIO(log_content.encode('utf-8'))
            log_file.seek(0)
            
            # ファイル名を生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ticket_log_{interaction.channel.name}_{timestamp}.txt"
            
            # ログをDMで送信
            try:
                await interaction.user.send(
                    content=f"📄 チケットログ: {interaction.channel.name}",
                    file=discord.File(log_file, filename=filename)
                )
                
                await interaction.followup.send(
                    "✅ ログをDMに送信しました!",
                    ephemeral=True
                )
            except discord.Forbidden:
                # DMが送信できない場合はチャンネルに送信
                log_file.seek(0)
                await interaction.channel.send(
                    content=f"📄 {interaction.user.mention} チケットログを生成しました:",
                    file=discord.File(log_file, filename=filename)
                )
                
                await interaction.followup.send(
                    "✅ ログをこのチャンネルに送信しました!(DMが無効のため)",
                    ephemeral=True
                )
            
            logger.info(f'{interaction.user.name}がチケットログを生成しました: {interaction.channel.name}')
        
        except Exception as e:
            await interaction.followup.send(
                f"❌ ログ生成中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'ログ生成エラー: {e}')
    
    @discord.ui.button(
        label="🗑️ チケット削除",
        style=discord.ButtonStyle.danger,
        custom_id="delete_ticket_button"
    )
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        """
        チケット削除ボタンが押された時の処理
        
        Args:
            interaction: インタラクション
            button: ボタン
        """
        # 管理者のみ削除可能
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ チケットを削除できるのは管理者のみです。",
                ephemeral=True
            )
            return
        
        try:
            # データベースから削除
            db = Database()
            await db.initialize()
            
            await db.connection.execute('''
                DELETE FROM tickets
                WHERE channel_id = ? AND guild_id = ?
            ''', (interaction.channel.id, interaction.guild_id))
            
            await db.connection.commit()
            
            # 削除通知を送信
            await interaction.response.send_message(
                "✅ 3秒後にこのチケットチャンネルを削除します...",
                ephemeral=True
            )
            
            # 3秒待機
            await asyncio.sleep(3)
            
            # チャンネルを削除
            await interaction.channel.delete(reason=f"チケット削除: {interaction.user.name}")
            
            logger.info(f'{interaction.user.name}がチケットチャンネルを削除しました: {interaction.channel.name}')
        
        except Exception as e:
            try:
                await interaction.followup.send(
                    f"❌ チケット削除中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
            except:
                pass
            logger.error(f'チケット削除エラー: {e}')


class TicketButton(View):
    """
    チケット作成ボタンのView
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        super().__init__(timeout=None)
        self.bot = bot
        self.db = Database()
    
    @discord.ui.button(
        label="🎫 チケットを作成",
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket_button"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        """
        チケット作成ボタンが押された時の処理
        
        Args:
            interaction: インタラクション
            button: ボタン
        """
        await self.db.initialize()
        
        # 既にチケットを持っているかチェック
        existing_tickets = []
        for channel in interaction.guild.text_channels:
            if channel.name.startswith(f"ticket-{interaction.user.name.lower()}"):
                existing_tickets.append(channel)
        
        if existing_tickets:
            await interaction.response.send_message(
                f"❌ 既にチケットが存在します: {existing_tickets[0].mention}",
                ephemeral=True
            )
            return
        
        try:
            # チケットカテゴリを取得または作成
            category = discord.utils.get(interaction.guild.categories, name="Tickets")
            if not category:
                category = await interaction.guild.create_category("Tickets")
            
            # チケットチャンネルの作成
            channel_name = f"ticket-{interaction.user.name.lower()}-{interaction.user.discriminator}"
            
            # 権限設定
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
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
                topic=f"チケット作成者: {interaction.user.name}"
            )
            
            # データベースに記録
            cursor = await self.db.connection.execute('''
                INSERT INTO tickets (guild_id, channel_id, creator_id, status)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild_id, ticket_channel.id, interaction.user.id, 'open'))
            
            ticket_id = cursor.lastrowid
            
            # ユーザー統計を更新
            await self.db.connection.execute('''
                INSERT INTO user_stats (guild_id, user_id, ticket_count, last_updated)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    ticket_count = ticket_count + 1,
                    last_updated = ?
            ''', (interaction.guild_id, interaction.user.id, datetime.now(), datetime.now()))
            
            await self.db.connection.commit()
            
            # チケットチャンネルにウェルカムメッセージを送信
            welcome_embed = discord.Embed(
                title=f"🎫 チケット #{ticket_id}",
                description=f"こんにちは、{interaction.user.mention}さん!\n"
                           f"このチケットは管理者とあなたのみが閲覧できます。\n"
                           f"ご用件を詳しくお書きください。",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            welcome_embed.add_field(name="ステータス", value="オープン", inline=True)
            welcome_embed.add_field(name="作成者", value=interaction.user.name, inline=True)
            welcome_embed.set_footer(text=f"Ticket ID: {ticket_id}")
            
            # クローズボタンのViewを作成
            close_view = TicketCloseButton(self.bot)
            
            await ticket_channel.send(
                content=f"{interaction.user.mention}",
                embed=welcome_embed,
                view=close_view
            )
            
            # ユーザーへの返信
            await interaction.response.send_message(
                f"✅ チケットを作成しました: {ticket_channel.mention}",
                ephemeral=True
            )
            
            logger.info(f'{interaction.user.name}がチケット#{ticket_id}を作成しました')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ チケット作成中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'チケット作成エラー: {e}')


class TicketPanel(commands.Cog):
    """
    チケットパネル管理コマンドのCog
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
    
    @app_commands.command(name="ticket_panel", description="チケットパネルの管理")
    @app_commands.describe(
        operation="操作を選択してください",
        channel="パネルを設置するチャンネル"
    )
    @app_commands.choices(operation=[
        app_commands.Choice(name="追加", value="add"),
        app_commands.Choice(name="削除", value="del")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        operation: app_commands.Choice[str],
        channel: discord.TextChannel
    ):
        """
        チケットパネル管理コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            operation: 操作(add/del)
            channel: 対象チャンネル
        """
        if operation.value == "add":
            # パネルのEmbedを作成
            panel_embed = discord.Embed(
                title="🎫 サポートチケット",
                description="サポートが必要な場合は、下のボタンをクリックしてチケットを作成してください。\n"
                           "専用のプライベートチャンネルが作成され、管理者とあなただけが会話できます。",
                color=discord.Color.blue()
            )
            
            panel_embed.add_field(
                name="📋 チケットの使い方",
                value="1. 下の「🎫 チケットを作成」ボタンをクリック\n"
                      "2. 専用チャンネルが作成されます\n"
                      "3. ご用件を詳しくお書きください\n"
                      "4. 管理者が対応します\n"
                      "5. 用件が解決したら「🔒 チケットをクローズ」ボタンをクリック",
                inline=False
            )
            
            panel_embed.add_field(
                name="⚠️ 注意事項",
                value="• 同時に複数のチケットは作成できません\n"
                      "• チケットは管理者または作成者がクローズできます\n"
                      "• クローズ後、管理者はログを生成できます\n"
                      "• チケットはクローズ後1週間で自動削除されます",
                inline=False
            )
            
            panel_embed.set_footer(text="サポートが必要な際はいつでもお気軽にご利用ください")
            
            # ボタンを追加してメッセージを送信
            view = TicketButton(self.bot)
            
            try:
                message = await channel.send(embed=panel_embed, view=view)
                
                # 成功メッセージ
                await interaction.response.send_message(
                    f"✅ {channel.mention}にチケットパネルを作成しました。",
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name}が{channel.name}にチケットパネルを作成しました')
            
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ 指定されたチャンネルにメッセージを送信する権限がありません。",
                    ephemeral=True
                )
        
        else:  # delete
            # チャンネル内のBotのメッセージを検索してパネルを削除
            try:
                deleted_count = 0
                async for message in channel.history(limit=100):
                    if message.author == self.bot.user and len(message.embeds) > 0:
                        embed = message.embeds[0]
                        if embed.title == "🎫 サポートチケット":
                            await message.delete()
                            deleted_count += 1
                
                if deleted_count > 0:
                    await interaction.response.send_message(
                        f"✅ {channel.mention}から{deleted_count}個のチケットパネルを削除しました。",
                        ephemeral=True
                    )
                    logger.info(f'{interaction.user.name}が{channel.name}からチケットパネルを削除しました')
                else:
                    await interaction.response.send_message(
                        f"❌ {channel.mention}にチケットパネルが見つかりませんでした。",
                        ephemeral=True
                    )
            
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ 指定されたチャンネルのメッセージを削除する権限がありません。",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ パネル削除中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'パネル削除エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(TicketPanel(bot))
    # 永続的なViewを登録
    bot.add_view(TicketButton(bot))
    bot.add_view(TicketCloseButton(bot))
    bot.add_view(TicketLogButton(bot))
