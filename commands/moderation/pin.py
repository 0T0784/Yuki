"""
/pin コマンド
メッセージを下部に固定します
"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import get_logger

logger = get_logger()


class Pin(commands.Cog):
    """
    メッセージ固定コマンドのCog
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
    
    @app_commands.command(name="pin", description="メッセージを下部に固定します")
    @app_commands.describe(
        message_id="固定するメッセージのID(オプション)",
        content="新規メッセージの内容(メッセージIDがない場合のみ)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def pin(
        self,
        interaction: discord.Interaction,
        message_id: str = None,
        content: str = None
    ):
        """
        メッセージ固定コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            message_id: メッセージID
            content: 新規メッセージ内容
        """
        # メッセージIDとコンテンツの両方がない場合はエラー
        if not message_id and not content:
            await interaction.response.send_message(
                "❌ メッセージIDまたは新規メッセージの内容を指定してください。",
                ephemeral=True
            )
            return
        
        # 両方指定されている場合はエラー
        if message_id and content:
            await interaction.response.send_message(
                "❌ メッセージIDと新規メッセージ内容は同時に指定できません。",
                ephemeral=True
            )
            return
        
        try:
            # メッセージIDが指定されている場合
            if message_id:
                try:
                    # メッセージを取得
                    message = await interaction.channel.fetch_message(int(message_id))
                    
                    # 既に固定されているかチェック
                    if message.pinned:
                        await interaction.response.send_message(
                            "❌ このメッセージは既に固定されています。",
                            ephemeral=True
                        )
                        return
                    
                    # メッセージを固定
                    await message.pin(reason=f"実行者: {interaction.user.name}")
                    
                    # 成功メッセージ
                    embed = discord.Embed(
                        title="📌 メッセージを固定しました",
                        description=f"[メッセージへジャンプ]({message.jump_url})",
                        color=discord.Color.green()
                    )
                    
                    embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
                    embed.add_field(name="メッセージID", value=message_id, inline=True)
                    
                    await interaction.response.send_message(embed=embed)
                    
                    logger.info(f'{interaction.user.name}がメッセージ(ID: {message_id})を固定しました')
                
                except discord.NotFound:
                    await interaction.response.send_message(
                        "❌ 指定されたIDのメッセージが見つかりません。",
                        ephemeral=True
                    )
                except ValueError:
                    await interaction.response.send_message(
                        "❌ メッセージIDは数字で指定してください。",
                        ephemeral=True
                    )
            
            # 新規メッセージの場合
            else:
                # 新規メッセージを送信
                sent_message = await interaction.channel.send(content)
                
                # メッセージを固定
                await sent_message.pin(reason=f"実行者: {interaction.user.name}")
                
                # 成功メッセージ
                embed = discord.Embed(
                    title="📌 メッセージを作成・固定しました",
                    description=f"[メッセージへジャンプ]({sent_message.jump_url})",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="実行者", value=interaction.user.mention, inline=True)
                embed.add_field(name="内容", value=content[:100] + "..." if len(content) > 100 else content, inline=False)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                logger.info(f'{interaction.user.name}が新規メッセージを作成・固定しました')
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ メッセージを固定する権限がありません。",
                ephemeral=True
            )
        except discord.HTTPException as e:
            if e.code == 50013:
                await interaction.response.send_message(
                    "❌ 固定できるメッセージの上限(50個)に達しています。古いメッセージの固定を解除してください。",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ メッセージ固定中にエラーが発生しました: {str(e)}",
                    ephemeral=True
                )
                logger.error(f'メッセージ固定エラー: {e}')
        except Exception as e:
            await interaction.response.send_message(
                f"❌ メッセージ固定中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'メッセージ固定エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Pin(bot))
