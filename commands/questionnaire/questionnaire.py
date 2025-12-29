"""
/questionnaire コマンド
アンケートの作成と終了を行います
"""

import discord
from discord import app_commands
from discord.ext import commands
import uuid
from datetime import datetime
from utils.logger import get_logger
from utils.database import Database

logger = get_logger()


class Questionnaire(commands.Cog):
    """
    アンケートコマンドのCog
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
    
    @app_commands.command(name="questionnaire_add", description="アンケートを作成します")
    @app_commands.describe(
        content="アンケートの内容",
        option1="選択肢1",
        option2="選択肢2",
        option3="選択肢3(オプション)"
    )
    async def questionnaire_add(
        self,
        interaction: discord.Interaction,
        content: str,
        option1: str,
        option2: str,
        option3: str = None
    ):
        """
        アンケート作成コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            content: アンケート内容
            option1: 選択肢1
            option2: 選択肢2
            option3: 選択肢3(オプション)
        """
        # UUIDでIDを生成
        questionnaire_id = str(uuid.uuid4())[:8]
        
        # 選択肢のリスト
        options = [option1, option2]
        if option3:
            options.append(option3)
        
        # リアクション絵文字
        reaction_emojis = ['1️⃣', '2️⃣', '3️⃣']
        
        try:
            # Embedの作成
            embed = discord.Embed(
                title="📋 アンケート",
                description=content,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # 選択肢を追加
            for i, option in enumerate(options):
                embed.add_field(
                    name=f"{reaction_emojis[i]} 選択肢{i+1}",
                    value=option,
                    inline=False
                )
            
            embed.add_field(
                name="📊 投票方法",
                value="リアクションをクリックして投票してください。",
                inline=False
            )
            
            embed.set_footer(text=f"ID: {questionnaire_id} | 作成者: {interaction.user.name}")
            
            # メッセージを送信
            message = await interaction.channel.send(embed=embed)
            
            # リアクションを追加
            for i in range(len(options)):
                await message.add_reaction(reaction_emojis[i])
            
            # データベースに保存
            await self.db.connection.execute('''
                INSERT INTO questionnaires
                (questionnaire_id, guild_id, channel_id, message_id, creator_id, content, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                questionnaire_id,
                interaction.guild_id,
                interaction.channel.id,
                message.id,
                interaction.user.id,
                content,
                'open'
            ))
            
            await self.db.connection.commit()
            
            # 成功メッセージ
            await interaction.response.send_message(
                f"✅ アンケートを作成しました!\nID: `{questionnaire_id}`",
                ephemeral=True
            )
            
            logger.info(f'{interaction.user.name}がアンケート({questionnaire_id})を作成しました')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ アンケート作成中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'アンケート作成エラー: {e}')
    
    @app_commands.command(name="questionnaire_close", description="アンケートを終了します")
    @app_commands.describe(
        questionnaire_id="アンケートID(省略すると最後に作成したアンケート)"
    )
    async def questionnaire_close(
        self,
        interaction: discord.Interaction,
        questionnaire_id: str = None
    ):
        """
        アンケート終了コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            questionnaire_id: アンケートID
        """
        try:
            # IDが指定されていない場合、最後に作成したアンケートを取得
            if not questionnaire_id:
                cursor = await self.db.connection.execute('''
                    SELECT questionnaire_id, channel_id, message_id
                    FROM questionnaires
                    WHERE guild_id = ? AND creator_id = ? AND status = 'open'
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (interaction.guild_id, interaction.user.id))
                
                row = await cursor.fetchone()
                
                if not row:
                    await interaction.response.send_message(
                        "❌ 終了可能なアンケートが見つかりません。",
                        ephemeral=True
                    )
                    return
                
                questionnaire_id, channel_id, message_id = row
            else:
                # 指定されたIDのアンケートを取得
                cursor = await self.db.connection.execute('''
                    SELECT channel_id, message_id, status
                    FROM questionnaires
                    WHERE questionnaire_id = ? AND guild_id = ?
                ''', (questionnaire_id, interaction.guild_id))
                
                row = await cursor.fetchone()
                
                if not row:
                    await interaction.response.send_message(
                        f"❌ ID `{questionnaire_id}` のアンケートが見つかりません。",
                        ephemeral=True
                    )
                    return
                
                channel_id, message_id, status = row
                
                if status == 'closed':
                    await interaction.response.send_message(
                        "❌ このアンケートは既に終了しています。",
                        ephemeral=True
                    )
                    return
            
            # メッセージを取得
            channel = interaction.guild.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message(
                    "❌ アンケートのチャンネルが見つかりません。",
                    ephemeral=True
                )
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "❌ アンケートのメッセージが見つかりません。",
                    ephemeral=True
                )
                return
            
            # リアクション数を集計
            reaction_emojis = ['1️⃣', '2️⃣', '3️⃣']
            results = {}
            
            for reaction in message.reactions:
                if str(reaction.emoji) in reaction_emojis:
                    # Botのリアクションを除外
                    count = reaction.count - 1
                    results[str(reaction.emoji)] = count
            
            # 結果のEmbedを作成
            result_embed = discord.Embed(
                title="🔒 アンケート終了",
                description=message.embeds[0].description if message.embeds else "アンケート",
                color=discord.Color.greyple(),
                timestamp=datetime.now()
            )
            
            # 結果を追加
            total_votes = sum(results.values())
            for emoji in reaction_emojis:
                if emoji in results:
                    votes = results[emoji]
                    percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                    result_embed.add_field(
                        name=f"{emoji}",
                        value=f"{votes}票 ({percentage:.1f}%)",
                        inline=True
                    )
            
            result_embed.add_field(
                name="📊 総投票数",
                value=f"{total_votes}票",
                inline=False
            )
            
            result_embed.set_footer(
                text=f"ID: {questionnaire_id} | 終了者: {interaction.user.name}"
            )
            
            # 元のメッセージを更新
            await message.edit(embed=result_embed)
            
            # リアクションをクリア
            await message.clear_reactions()
            
            # データベースを更新
            await self.db.connection.execute('''
                UPDATE questionnaires
                SET status = 'closed'
                WHERE questionnaire_id = ?
            ''', (questionnaire_id,))
            
            await self.db.connection.commit()
            
            # 成功メッセージ
            await interaction.response.send_message(
                f"✅ アンケート(ID: `{questionnaire_id}`)を終了しました。",
                ephemeral=True
            )
            
            logger.info(f'{interaction.user.name}がアンケート({questionnaire_id})を終了しました')
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ アンケート終了中にエラーが発生しました: {str(e)}",
                ephemeral=True
            )
            logger.error(f'アンケート終了エラー: {e}')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Questionnaire(bot))