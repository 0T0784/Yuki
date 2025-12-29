"""
/role コマンド
管理者ロールとBotロールの追加/削除を行います
"""

import discord
from discord import app_commands
from discord.ext import commands
import json
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Role(commands.Cog):
    """
    ロール管理コマンドのCog
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
    
    @app_commands.command(name="role", description="管理者ロールとBotロールの管理")
    @app_commands.describe(
        operation="操作を選択してください",
        role_type="ロールタイプを選択してください",
        role="対象のロールを選択してください"
    )
    @app_commands.choices(
        operation=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="del")
        ],
        role_type=[
            app_commands.Choice(name="管理者ロール", value="administrator"),
            app_commands.Choice(name="Botロール", value="bot")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def role(
        self,
        interaction: discord.Interaction,
        operation: app_commands.Choice[str],
        role_type: app_commands.Choice[str],
        role: discord.Role
    ):
        """
        ロール管理コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            operation: 操作(add/del)
            role_type: ロールタイプ(administrator/bot)
            role: 対象ロール
        """
        # データベースのカラム名を決定
        column_name = 'admin_role_ids' if role_type.value == 'administrator' else 'bot_role_ids'
        
        try:
            # 現在の設定を取得
            cursor = await self.db.connection.execute(f'''
                SELECT {column_name} FROM guild_settings
                WHERE guild_id = ?
            ''', (interaction.guild_id,))
            
            row = await cursor.fetchone()
            
            # 現在のロールIDリストを取得
            if row and row[0]:
                role_ids = json.loads(row[0])
            else:
                role_ids = []
            
            # 操作に応じて処理
            if operation.value == 'add':
                # 既に追加されているかチェック
                if role.id in role_ids:
                    await interaction.response.send_message(
                        f"❌ {role.mention}は既に{role_type.name}として登録されています。",
                        ephemeral=True
                    )
                    return
                
                # ロールIDを追加
                role_ids.append(role.id)
                
                # データベースに保存
                await self.db.connection.execute(f'''
                    INSERT INTO guild_settings (guild_id, {column_name})
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET
                        {column_name} = ?
                ''', (interaction.guild_id, json.dumps(role_ids), json.dumps(role_ids)))
                
                await self.db.connection.commit()
                
                # 成功メッセージ
                embed = discord.Embed(
                    title="✅ ロール追加完了",
                    description=f"{role.mention}を{role_type.name}として追加しました。",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="ロール", value=role.mention, inline=True)
                embed.add_field(name="タイプ", value=role_type.name, inline=True)
                embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
                
                await interaction.response.send_message(embed=embed)
                logger.info(f'{interaction.user.name}が{role.name}を{role_type.name}として追加しました')
                
            else:  # delete
                # 登録されているかチェック
                if role.id not in role_ids:
                    await interaction.response.send_message(
                        f"❌ {role.mention}は{role_type.name}として登録されていません。",
                        ephemeral=True
                    )
                    return
                
                # ロールIDを削除
                role_ids.remove(role.id)
                
                # データベースに保存
                await self.db.connection.execute(f'''
                    UPDATE guild_settings
                    SET {column_name} = ?
                    WHERE guild_id = ?
                ''', (json.dumps(role_ids), interaction.guild_id))
                
                await self.db.connection.commit()
                
                # 成功メッセージ
                embed = discord.Embed(
                    title="✅ ロール削除完了",
                    description=f"{role.mention}を{role_type.name}から削除しました。",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="ロール", value=role.mention, inline=True)
                embed.add_field(name="タイプ", value=role_type.name, inline=True)
                embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
                
                await interaction.response.send_message(embed=embed)
                logger.info(f'{interaction.user.name}が{role.name}を{role_type.name}から削除しました')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ エラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'ロール管理エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Role(bot))
