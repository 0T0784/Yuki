"""
Discord Bot メインファイル
このファイルはBotの起動とコマンドの登録を行います
"""

import discord
from discord.ext import commands
import os
import asyncio
import signal
import sys
from dotenv import load_dotenv
from utils.logger import setup_logger
from utils.database import Database
from utils.keep_alive import keep_alive

# 環境変数の読み込み
load_dotenv()

# ロガーのセットアップ
logger = setup_logger()

# Botのインテント設定
intents = discord.Intents.all()  # すべてのインテントを有効化
intents.message_content = True  # メッセージ内容の取得
intents.members = True  # メンバー情報の取得
intents.guilds = True  # サーバー情報の取得

# Botクラスの初期化
bot = commands.Bot(command_prefix="!", intents=intents)

# データベースの初期化
db = Database()

# シャットダウンフラグ
shutdown_flag = False


def signal_handler(sig, frame):
    """
    Ctrl+Cなどのシグナルを受け取った時の処理
    
    Args:
        sig: シグナル
        frame: フレーム
    """
    global shutdown_flag
    logger.info('終了シグナルを受信しました。Botをシャットダウンします...')
    shutdown_flag = True


# シグナルハンドラーの登録
signal.signal(signal.SIGINT, signal_handler)
if sys.platform != 'win32':
    signal.signal(signal.SIGTERM, signal_handler)


@bot.event
async def on_ready():
    """
    Botが起動した際に実行されるイベント
    """
    logger.info(f'Botが起動しました: {bot.user.name} (ID: {bot.user.id})')
    
    # データベースの初期化
    await db.initialize()
    logger.info('データベースの初期化が完了しました')
    
    # スラッシュコマンドの同期
    try:
        synced = await bot.tree.sync()
        logger.info(f'{len(synced)}個のコマンドを同期しました')
    except Exception as e:
        logger.error(f'コマンドの同期に失敗しました: {e}')
    
    # Botのステータス設定
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/help でコマンド一覧"
        )
    )


@bot.event
async def on_guild_join(guild):
    """
    Botが新しいサーバーに追加された際に実行されるイベント
    """
    logger.info(f'新しいサーバーに参加しました: {guild.name} (ID: {guild.id})')
    # サーバーのデータベース初期化
    await db.initialize_guild(guild.id)


@bot.event
async def on_message(message):
    """
    メッセージが送信された際に実行されるイベント
    統計情報の記録を行います
    """
    # Bot自身のメッセージは無視
    if message.author.bot:
        return
    
    # 統計情報の記録
    if message.guild:
        try:
            await db.increment_user_message_count(
                guild_id=message.guild.id,
                user_id=message.author.id
            )
        except Exception as e:
            logger.error(f'メッセージカウント更新エラー: {e}')
    
    # コマンド処理
    await bot.process_commands(message)


async def load_extensions():
    """
    コマンドのCogを読み込む関数
    """
    extensions = [
        # 基礎機能系コマンド
        'commands.basic.info',
        'commands.basic.help',
        'commands.basic.ping',
        
        # 管理者系コマンド
        'commands.admin.role',
        
        # 管理系コマンド
        'commands.moderation.timeout',
        'commands.moderation.kick',
        'commands.moderation.ban',
        'commands.moderation.report',
        'commands.moderation.pin',
        
        # チケット系コマンド
        'commands.ticket.ticket_panel',
        'commands.ticket.ticket',
        
        # 統計系コマンド
        'commands.stats.stats',
        'commands.stats.stats_send',
        
        # 投票・アンケート系コマンド
        'commands.questionnaire.questionnaire',
        
        # ログ系コマンド
        'commands.logs.logs',
        
        # リアクションロール系コマンド
        'commands.roles.reactionrole',
    ]
    
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'{extension} を読み込みました')
        except Exception as e:
            logger.error(f'{extension} の読み込みに失敗しました: {e}')
    
    logger.info('すべてのコマンドの読み込みが完了しました')


async def main():
    """
    メイン関数
    """
    try:
        async with bot:
            # Cogの読み込み
            await load_extensions()
            
            # Koyeb用のキープアライブサーバー起動
            keep_alive()
            
            # Botの起動
            token = os.getenv('DISCORD_TOKEN')
            if not token:
                logger.error('DISCORD_TOKENが設定されていません')
                logger.error('.envファイルを確認してください')
                return
            
            logger.info('Botを起動しています...')
            await bot.start(token)
    
    except KeyboardInterrupt:
        logger.info('キーボード割り込みを検出しました')
    except Exception as e:
        logger.error(f'Bot起動中にエラーが発生しました: {e}')
    finally:
        # クリーンアップ処理
        logger.info('クリーンアップを実行しています...')
        
        if not bot.is_closed():
            await bot.close()
        
        # データベース接続を閉じる
        try:
            await db.close()
            logger.info('データベース接続を閉じました')
        except Exception as e:
            logger.error(f'データベースクローズエラー: {e}')
        
        logger.info('Botが正常に終了しました')


if __name__ == '__main__':
    try:
        # イベントループポリシーの設定(Windows用)
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Botの起動
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n✅ Botを終了しました')
    except Exception as e:
        logger.error(f'予期しないエラーが発生しました: {e}')
        sys.exit(1)
