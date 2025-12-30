"""
/reactionrole コマンド
リアクションロール機能を実装します
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class ReactionRole(commands.Cog):
    """
    リアクションロールコマンドのCog
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
        # リアクションロール用のテーブルを作成
        await self._create_reaction_role_table()
    
    async def _create_reaction_role_table(self):
        """
        リアクションロール用のテーブルを作成
        """
        await self.db.connection.execute('''
            CREATE TABLE IF NOT EXISTS reaction_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                message_id INTEGER,
                emoji TEXT,
                role_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, emoji)
            )
        ''')
        await self.db.connection.commit()
    
    @app_commands.command(name="reactionrole", description="リアクションロールパネルを作成します")
    @app_commands.describe(
        title="パネルのタイトル",
        description="パネルの説明",
        channel="パネルを設置するチャンネル"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reactionrole(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        channel: discord.TextChannel
    ):
        """
        リアクションロールパネル作成コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            title: タイトル
            description: 説明
            channel: 対象チャンネル
        """
        try:
            # Embedの作成
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.set_footer(text="リアクションを押してロールを取得/解除できます")
            
            # メッセージを送信
            message = await channel.send(embed=embed)
            
            # 成功メッセージ
            success_embed = discord.Embed(
                title="✅ リアクションロールパネルを作成しました",
                description=f"パネル: {message.jump_url}\n\n"
                           f"次に `/reactionrole_add` コマンドでロールを追加してください。",
                color=discord.Color.green()
            )
            
            success_embed.add_field(
                name="📝 メッセージID",
                value=f"`{message.id}`",
                inline=False
            )
            
            success_embed.add_field(
                name="📌 使い方",
                value=f"1. `/reactionrole_add {message.id} 絵文字 @ロール` を実行\n"
                      f"2. 複数のロールを追加可能\n"
                      f"3. ユーザーがリアクションを押すとロールが付与されます",
                inline=False
            )
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
            logger.info(f'{interaction.user.name}がリアクションロールパネルを作成しました')
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ 指定されたチャンネルにメッセージを送信する権限がありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ パネル作成中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'リアクションロールパネル作成エラー: {e}')
    
    @app_commands.command(name="reactionrole_add", description="リアクションロールを追加します")
    @app_commands.describe(
        message_id="メッセージID",
        emoji="リアクション絵文字",
        role="付与するロール"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reactionrole_add(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        """
        リアクションロール追加コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            message_id: メッセージID
            emoji: 絵文字
            role: ロール
        """
        try:
            # メッセージを取得
            message = None
            for channel in interaction.guild.text_channels:
                try:
                    message = await channel.fetch_message(int(message_id))
                    break
                except (discord.NotFound, discord.Forbidden):
                    continue
                except ValueError:
                    await interaction.response.send_message(
                        "❌ メッセージIDは数字で指定してください。",
                        ephemeral=True
                    )
                    return
            
            if not message:
                await interaction.response.send_message(
                    "❌ 指定されたIDのメッセージが見つかりません。",
                    ephemeral=True
                )
                return
            
            # ロールがBotより上位かチェック
            if role.position >= interaction.guild.me.top_role.position:
                await interaction.response.send_message(
                    "❌ このロールはBotのロールより上位にあるため付与できません。\n"
                    "Botのロールを対象ロールより上に移動してください。",
                    ephemeral=True
                )
                return
            
            # 既に登録されているかチェック
            cursor = await self.db.connection.execute('''
                SELECT id FROM reaction_roles
                WHERE message_id = ? AND emoji = ?
            ''', (message.id, emoji))
            
            existing = await cursor.fetchone()
            
            if existing:
                # 既存の設定を更新
                await self.db.connection.execute('''
                    UPDATE reaction_roles
                    SET role_id = ?
                    WHERE message_id = ? AND emoji = ?
                ''', (role.id, message.id, emoji))
                action = "更新"
            else:
                # 新規登録
                await self.db.connection.execute('''
                    INSERT INTO reaction_roles
                    (guild_id, channel_id, message_id, emoji, role_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    interaction.guild_id,
                    message.channel.id,
                    message.id,
                    emoji,
                    role.id
                ))
                action = "追加"
            
            await self.db.connection.commit()
            
            # メッセージにリアクションを追加
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException as e:
                logger.warning(f'リアクション追加失敗: {e}')
            
            # Embedを更新(ロール一覧を追加)
            if message.embeds:
                embed = message.embeds[0]
                
                # 既存のロール情報をクリア
                new_fields = []
                for field in embed.fields:
                    if not field.name.startswith("🎭"):
                        new_fields.append(field)
                
                embed.clear_fields()
                for field in new_fields:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
                
                # 現在のリアクションロール一覧を取得
                cursor = await self.db.connection.execute('''
                    SELECT emoji, role_id FROM reaction_roles
                    WHERE message_id = ?
                    ORDER BY created_at
                ''', (message.id,))
                
                roles_list = await cursor.fetchall()
                
                if roles_list:
                    roles_text = ""
                    for emoji_db, role_id in roles_list:
                        role_obj = interaction.guild.get_role(role_id)
                        if role_obj:
                            roles_text += f"{emoji_db} → {role_obj.mention}\n"
                    
                    embed.add_field(
                        name="🎭 利用可能なロール",
                        value=roles_text,
                        inline=False
                    )
                
                await message.edit(embed=embed)
            
            # 成功メッセージ
            await interaction.response.send_message(
                f"✅ リアクションロールを{action}しました!\n"
                f"絵文字: {emoji}\n"
                f"ロール: {role.mention}\n"
                f"メッセージ: {message.jump_url}",
                ephemeral=True
            )
            
            logger.info(f'{interaction.user.name}がリアクションロールを{action}しました: {emoji} → {role.name}')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リアクションロール追加中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'リアクションロール追加エラー: {e}')
    
    @app_commands.command(name="reactionrole_remove", description="リアクションロールを削除します")
    @app_commands.describe(
        message_id="メッセージID",
        emoji="削除するリアクション絵文字"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reactionrole_remove(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str
    ):
        """
        リアクションロール削除コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            message_id: メッセージID
            emoji: 絵文字
        """
        try:
            # データベースから削除
            cursor = await self.db.connection.execute('''
                DELETE FROM reaction_roles
                WHERE message_id = ? AND emoji = ?
                RETURNING role_id
            ''', (int(message_id), emoji))
            
            deleted = await cursor.fetchone()
            await self.db.connection.commit()
            
            if not deleted:
                await interaction.response.send_message(
                    "❌ 指定されたリアクションロールが見つかりません。",
                    ephemeral=True
                )
                return
            
            # メッセージからリアクションを削除
            message = None
            for channel in interaction.guild.text_channels:
                try:
                    message = await channel.fetch_message(int(message_id))
                    break
                except (discord.NotFound, discord.Forbidden):
                    continue
            
            if message:
                try:
                    await message.clear_reaction(emoji)
                except discord.HTTPException:
                    pass
            
            await interaction.response.send_message(
                f"✅ リアクションロール({emoji})を削除しました。",
                ephemeral=True
            )
            
            logger.info(f'{interaction.user.name}がリアクションロールを削除しました: {emoji}')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リアクションロール削除中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'リアクションロール削除エラー: {e}')
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        リアクションが追加された時のイベント
        
        Args:
            payload: リアクションイベント
        """
        # Botのリアクションは無視
        if payload.user_id == self.bot.user.id:
            return
        
        # リアクションロールをチェック
        cursor = await self.db.connection.execute('''
            SELECT role_id FROM reaction_roles
            WHERE message_id = ? AND emoji = ?
        ''', (payload.message_id, str(payload.emoji)))
        
        row = await cursor.fetchone()
        
        if row:
            role_id = row[0]
            guild = self.bot.get_guild(payload.guild_id)
            
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.add_roles(role, reason="リアクションロール")
                        logger.info(f'{member.name}にロール{role.name}を付与しました')
                    except discord.Forbidden:
                        logger.error(f'ロール付与権限がありません: {role.name}')
                    except Exception as e:
                        logger.error(f'ロール付与エラー: {e}')
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        リアクションが削除された時のイベント
        
        Args:
            payload: リアクションイベント
        """
        # Botのリアクションは無視
        if payload.user_id == self.bot.user.id:
            return
        
        # リアクションロールをチェック
        cursor = await self.db.connection.execute('''
            SELECT role_id FROM reaction_roles
            WHERE message_id = ? AND emoji = ?
        ''', (payload.message_id, str(payload.emoji)))
        
        row = await cursor.fetchone()
        
        if row:
            role_id = row[0]
            guild = self.bot.get_guild(payload.guild_id)
            
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.remove_roles(role, reason="リアクションロール解除")
                        logger.info(f'{member.name}からロール{role.name}を削除しました')
                    except discord.Forbidden:
                        logger.error(f'ロール削除権限がありません: {role.name}')
                    except Exception as e:
                        logger.error(f'ロール削除エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(ReactionRole(bot))
