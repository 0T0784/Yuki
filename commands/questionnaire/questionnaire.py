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
        # アンケート参加者テーブルを作成
        await self._create_questionnaire_participants_table()
    
    async def _create_questionnaire_participants_table(self):
        """
        アンケート参加者テーブルを作成
        """
        await self.db.connection.execute('''
            CREATE TABLE IF NOT EXISTS questionnaire_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questionnaire_id TEXT,
                user_id INTEGER,
                emoji TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(questionnaire_id, user_id, emoji)
            )
        ''')
        
        # questionnairesテーブルにpublic_resultsカラムを追加(既存の場合はエラーを無視)
        try:
            await self.db.connection.execute('''
                ALTER TABLE questionnaires ADD COLUMN public_results BOOLEAN DEFAULT FALSE
            ''')
        except:
            pass  # カラムが既に存在する場合は無視
        
        await self.db.connection.commit()
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        リアクションが追加された時のイベント
        終了したアンケートへのリアクションを防ぎ、参加者を記録
        
        Args:
            payload: リアクションイベント
        """
        # Bot自身のリアクションは無視
        if payload.user_id == self.bot.user.id:
            return
        
        # このメッセージがアンケートかチェック
        cursor = await self.db.connection.execute('''
            SELECT questionnaire_id, status FROM questionnaires
            WHERE message_id = ? AND guild_id = ?
        ''', (payload.message_id, payload.guild_id))
        
        row = await cursor.fetchone()
        
        if row:
            questionnaire_id, status = row
            
            # 終了したアンケートの場合、リアクションを削除
            if status == 'closed':
                try:
                    guild = self.bot.get_guild(payload.guild_id)
                    if guild:
                        channel = guild.get_channel(payload.channel_id)
                        if channel:
                            message = await channel.fetch_message(payload.message_id)
                            user = guild.get_member(payload.user_id)
                            if user and message:
                                # ユーザーのリアクションを削除
                                await message.remove_reaction(payload.emoji, user)
                                
                                # ユーザーにDMで通知
                                try:
                                    await user.send(
                                        f"⚠️ このアンケートは既に終了しています。\n"
                                        f"リアクションを追加することはできません。\n"
                                        f"メッセージ: {message.jump_url}"
                                    )
                                except discord.Forbidden:
                                    pass
                                
                                logger.info(
                                    f'{user.name}が終了したアンケートにリアクションを追加しようとしました '
                                    f'(メッセージID: {payload.message_id})'
                                )
                except Exception as e:
                    logger.error(f'終了アンケートのリアクション削除エラー: {e}')
            
            # オープンなアンケートの場合、参加者を記録
            elif status == 'open':
                try:
                    await self.db.connection.execute('''
                        INSERT OR IGNORE INTO questionnaire_participants
                        (questionnaire_id, user_id, emoji)
                        VALUES (?, ?, ?)
                    ''', (questionnaire_id, payload.user_id, str(payload.emoji)))
                    await self.db.connection.commit()
                except Exception as e:
                    logger.error(f'アンケート参加者記録エラー: {e}')
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        リアクションが削除された時のイベント
        参加者記録を削除
        
        Args:
            payload: リアクションイベント
        """
        # Bot自身のリアクションは無視
        if payload.user_id == self.bot.user.id:
            return
        
        # このメッセージがアンケートかチェック
        cursor = await self.db.connection.execute('''
            SELECT questionnaire_id, status FROM questionnaires
            WHERE message_id = ? AND guild_id = ?
        ''', (payload.message_id, payload.guild_id))
        
        row = await cursor.fetchone()
        
        if row:
            questionnaire_id, status = row
            
            # オープンなアンケートの場合のみ削除
            if status == 'open':
                try:
                    await self.db.connection.execute('''
                        DELETE FROM questionnaire_participants
                        WHERE questionnaire_id = ? AND user_id = ? AND emoji = ?
                    ''', (questionnaire_id, payload.user_id, str(payload.emoji)))
                    await self.db.connection.commit()
                except Exception as e:
                    logger.error(f'アンケート参加者削除エラー: {e}')
    
    @app_commands.command(name="questionnaire_add", description="アンケートを作成します")
    @app_commands.describe(
        content="アンケートの内容",
        option1="選択肢1",
        option2="選択肢2",
        option3="選択肢3(オプション)",
        emoji1="選択肢1の絵文字(デフォルト: 1️⃣)",
        emoji2="選択肢2の絵文字(デフォルト: 2️⃣)",
        emoji3="選択肢3の絵文字(デフォルト: 3️⃣)",
        public_results="結果を公開するか(参加者名を表示)"
    )
    async def questionnaire_add(
        self,
        interaction: discord.Interaction,
        content: str,
        option1: str,
        option2: str,
        option3: str = None,
        emoji1: str = "1️⃣",
        emoji2: str = "2️⃣",
        emoji3: str = "3️⃣",
        public_results: bool = False
    ):
        """
        アンケート作成コマンドのメイン処理
        
        Args:
            interaction: インタラクション
            content: アンケート内容
            option1: 選択肢1
            option2: 選択肢2
            option3: 選択肢3(オプション)
            emoji1: 選択肢1の絵文字
            emoji2: 選択肢2の絵文字
            emoji3: 選択肢3の絵文字
            public_results: 結果公開フラグ
        """
        # UUIDでIDを生成
        questionnaire_id = str(uuid.uuid4())[:8]
        
        # 選択肢のリスト
        options = [option1, option2]
        emojis = [emoji1, emoji2]
        
        if option3:
            options.append(option3)
            emojis.append(emoji3)
        
        try:
            # Embedの作成
            embed = discord.Embed(
                title="📋 アンケート",
                description=content,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # 選択肢を追加
            for i, (option, emoji) in enumerate(zip(options, emojis)):
                embed.add_field(
                    name=f"{emoji} 選択肢{i+1}",
                    value=option,
                    inline=False
                )
            
            embed.add_field(
                name="📊 投票方法",
                value="リアクションをクリックして投票してください。",
                inline=False
            )
            
            # 公開/非公開を表示
            result_type = "🔓 公開（参加者名を表示）" if public_results else "🔒 非公開（人数のみ表示）"
            embed.add_field(
                name="📢 結果表示",
                value=result_type,
                inline=False
            )
            
            embed.set_footer(text=f"ID: {questionnaire_id} | 作成者: {interaction.user.name}")
            
            # メッセージを送信
            message = await interaction.channel.send(embed=embed)
            
            # リアクションを追加
            for emoji in emojis:
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException as e:
                    logger.warning(f'リアクション追加失敗 ({emoji}): {e}')
            
            # データベースに保存
            await self.db.connection.execute('''
                INSERT INTO questionnaires
                (questionnaire_id, guild_id, channel_id, message_id, creator_id, content, status, public_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                questionnaire_id,
                interaction.guild_id,
                interaction.channel.id,
                message.id,
                interaction.user.id,
                content,
                'open',
                public_results
            ))
            
            await self.db.connection.commit()
            
            # 成功メッセージ
            await interaction.response.send_message(
                f"✅ アンケートを作成しました!\n"
                f"ID: `{questionnaire_id}`\n"
                f"結果表示: {result_type}",
                ephemeral=True
            )
            
            logger.info(f'{interaction.user.name}がアンケート({questionnaire_id})を作成しました (公開: {public_results})')
        
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
                    SELECT questionnaire_id, channel_id, message_id, public_results
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
                
                questionnaire_id, channel_id, message_id, public_results = row
            else:
                # 指定されたIDのアンケートを取得
                cursor = await self.db.connection.execute('''
                    SELECT channel_id, message_id, status, public_results
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
                
                channel_id, message_id, status, public_results = row
                
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
            results = {}
            total_votes = 0
            
            for reaction in message.reactions:
                # Botのリアクションを除外
                count = reaction.count - 1
                if count > 0:
                    results[str(reaction.emoji)] = count
                    total_votes += count
            
            # 結果のEmbedを作成
            result_embed = discord.Embed(
                title="🔒 アンケート終了",
                description=message.embeds[0].description if message.embeds else "アンケート",
                color=discord.Color.greyple(),
                timestamp=datetime.now()
            )
            
            # 元のEmbedから選択肢情報を取得して結果を表示
            if message.embeds and message.embeds[0].fields:
                for field in message.embeds[0].fields:
                    if "選択肢" in field.name:
                        # 絵文字を抽出
                        emoji = field.name.split()[0] if field.name else "❓"
                        votes = results.get(emoji, 0)
                        percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                        
                        # 参加者リストを取得
                        if public_results:
                            cursor = await self.db.connection.execute('''
                                SELECT user_id FROM questionnaire_participants
                                WHERE questionnaire_id = ? AND emoji = ?
                                ORDER BY added_at
                            ''', (questionnaire_id, emoji))
                            
                            participants = await cursor.fetchall()
                            
                            # 参加者名を取得
                            participant_names = []
                            for (user_id,) in participants:
                                member = interaction.guild.get_member(user_id)
                                if member:
                                    participant_names.append(member.display_name)
                            
                            # 参加者リストを作成（全員表示）
                            if participant_names:
                                participants_text = ", ".join(participant_names)
                                
                                # Discordの制限（フィールド値は1024文字まで）を考慮
                                # 選択肢の説明と投票情報を含めて1024文字以内に収める
                                base_text = f"{field.value}\n**{votes}票 ({percentage:.1f}%)**\n👥 "
                                max_participants_length = 1024 - len(base_text) - 50  # 余裕を持たせる
                                
                                if len(participants_text) > max_participants_length:
                                    # 文字数制限を超える場合は、可能な限り多くの名前を表示
                                    truncated_text = participants_text[:max_participants_length]
                                    # 最後のカンマで切る
                                    last_comma = truncated_text.rfind(", ")
                                    if last_comma > 0:
                                        truncated_text = truncated_text[:last_comma]
                                    
                                    # 残りの人数を計算
                                    displayed_count = truncated_text.count(",") + 1
                                    remaining_count = len(participant_names) - displayed_count
                                    participants_text = f"{truncated_text} ...他{remaining_count}名"
                            else:
                                participants_text = "なし"
                            
                            result_embed.add_field(
                                name=field.name,
                                value=f"{field.value}\n"
                                      f"**{votes}票 ({percentage:.1f}%)**\n"
                                      f"👥 {participants_text}",
                                inline=False
                            )
                        else:
                            # 非公開の場合は人数と割合のみ
                            result_embed.add_field(
                                name=field.name,
                                value=f"{field.value}\n"
                                      f"**{votes}票 ({percentage:.1f}%)**",
                                inline=False
                            )
            
            result_embed.add_field(
                name="📊 総投票数",
                value=f"{total_votes}票",
                inline=False
            )
            
            # 公開/非公開を表示
            result_type = "🔓 公開結果" if public_results else "🔒 非公開結果"
            result_embed.add_field(
                name="📢 結果表示",
                value=result_type,
                inline=False
            )
            
            result_embed.set_footer(
                text=f"ID: {questionnaire_id} | 終了者: {interaction.user.name}"
            )
            
            # 元のメッセージを更新
            await message.edit(embed=result_embed)
            
            # リアクションをクリア
            await message.clear_reactions()
            
            # 公開モードで参加者が多い場合、詳細な参加者リストを別メッセージで送信
            if public_results and total_votes > 0:
                detailed_participants = []
                
                # 各選択肢ごとの参加者を取得
                if message.embeds and message.embeds[0].fields:
                    for field in message.embeds[0].fields:
                        if "選択肢" in field.name:
                            emoji = field.name.split()[0] if field.name else "❓"
                            
                            cursor = await self.db.connection.execute('''
                                SELECT user_id FROM questionnaire_participants
                                WHERE questionnaire_id = ? AND emoji = ?
                                ORDER BY added_at
                            ''', (questionnaire_id, emoji))
                            
                            participants = await cursor.fetchall()
                            
                            if participants:
                                participant_names = []
                                for (user_id,) in participants:
                                    member = interaction.guild.get_member(user_id)
                                    if member:
                                        participant_names.append(member.display_name)
                                
                                if participant_names:
                                    detailed_participants.append({
                                        'emoji': emoji,
                                        'name': field.name,
                                        'names': participant_names
                                    })
                
                # 詳細リストのEmbedを作成
                if detailed_participants:
                    detail_embed = discord.Embed(
                        title="📋 詳細な参加者リスト",
                        description=f"アンケートID: `{questionnaire_id}`",
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    
                    for item in detailed_participants:
                        # 改行で区切って見やすく
                        names_list = "\n".join([f"• {name}" for name in item['names']])
                        
                        # 1フィールドあたり1024文字制限があるので、分割が必要な場合は複数フィールドに
                        if len(names_list) > 1000:
                            # 複数フィールドに分割
                            chunks = []
                            current_chunk = []
                            current_length = 0
                            
                            for name in item['names']:
                                name_line = f"• {name}\n"
                                if current_length + len(name_line) > 1000:
                                    chunks.append("\n".join([f"• {n}" for n in current_chunk]))
                                    current_chunk = [name]
                                    current_length = len(name_line)
                                else:
                                    current_chunk.append(name)
                                    current_length += len(name_line)
                            
                            if current_chunk:
                                chunks.append("\n".join([f"• {n}" for n in current_chunk]))
                            
                            # 各チャンクをフィールドとして追加
                            for i, chunk in enumerate(chunks):
                                field_name = f"{item['name']}" if i == 0 else f"{item['name']} (続き{i})"
                                detail_embed.add_field(
                                    name=field_name,
                                    value=chunk,
                                    inline=False
                                )
                        else:
                            detail_embed.add_field(
                                name=item['name'],
                                value=names_list,
                                inline=False
                            )
                    
                    detail_embed.set_footer(text="アンケート詳細情報")
                    
                    # 詳細リストを送信
                    await message.channel.send(embed=detail_embed)
            
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
