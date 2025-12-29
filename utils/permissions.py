"""
権限チェックユーティリティ
ユーザーの権限を確認するヘルパー関数
"""

import discord
from utils.database import Database
from utils.logger import get_logger

logger = get_logger()


async def is_administrator(member: discord.Member) -> bool:
    """
    ユーザーが管理者権限を持っているかチェック
    
    Args:
        member: チェック対象のメンバー
        
    Returns:
        bool: 管理者権限を持っている場合True
    """
    # サーバーオーナーは常に管理者
    if member.guild.owner_id == member.id:
        return True
    
    # Discord標準の管理者権限を持っている
    if member.guild_permissions.administrator:
        return True
    
    # データベースに登録された管理者ロールを持っている
    db = Database()
    await db.initialize()
    
    try:
        cursor = await db.connection.execute('''
            SELECT admin_role_ids FROM guild_settings
            WHERE guild_id = ?
        ''', (member.guild.id,))
        
        row = await cursor.fetchone()
        
        if row and row[0]:
            # JSONから管理者ロールIDのリストを取得
            import json
            admin_role_ids = json.loads(row[0]) if row[0] else []
            
            # ユーザーが管理者ロールを持っているかチェック
            user_role_ids = [role.id for role in member.roles]
            return any(role_id in admin_role_ids for role_id in user_role_ids)
        
        return False
        
    except Exception as e:
        logger.error(f'管理者チェックエラー: {e}')
        return False


async def is_bot_role(member: discord.Member) -> bool:
    """
    ユーザーがBotロールを持っているかチェック
    
    Args:
        member: チェック対象のメンバー
        
    Returns:
        bool: Botロールを持っている場合True
    """
    db = Database()
    await db.initialize()
    
    try:
        cursor = await db.connection.execute('''
            SELECT bot_role_ids FROM guild_settings
            WHERE guild_id = ?
        ''', (member.guild.id,))
        
        row = await cursor.fetchone()
        
        if row and row[0]:
            # JSONからBotロールIDのリストを取得
            import json
            bot_role_ids = json.loads(row[0]) if row[0] else []
            
            # ユーザーがBotロールを持っているかチェック
            user_role_ids = [role.id for role in member.roles]
            return any(role_id in bot_role_ids for role_id in user_role_ids)
        
        return False
        
    except Exception as e:
        logger.error(f'Botロールチェックエラー: {e}')
        return False


async def can_moderate(moderator: discord.Member, target: discord.Member) -> bool:
    """
    モデレーターが対象ユーザーをモデレートできるかチェック
    
    Args:
        moderator: モデレーター
        target: 対象ユーザー
        
    Returns:
        bool: モデレート可能な場合True
    """
    # 自分自身はモデレートできない
    if moderator.id == target.id:
        return False
    
    # Botはモデレートできない
    if target.bot:
        return False
    
    # サーバーオーナーはモデレートできない
    if target.id == moderator.guild.owner_id:
        return False
    
    # 管理者はモデレートできない(モデレーターが管理者でない限り)
    if target.guild_permissions.administrator:
        return await is_administrator(moderator)
    
    # モデレーターの最高ロールが対象ユーザーより上位である必要がある
    if moderator.top_role <= target.top_role:
        return False
    
    return True


async def get_log_channel(guild: discord.Guild, log_type: str) -> discord.TextChannel:
    """
    指定されたログタイプのチャンネルを取得
    
    Args:
        guild: サーバー
        log_type: ログタイプ('public', 'private', 'report')
        
    Returns:
        discord.TextChannel: ログチャンネル(見つからない場合None)
    """
    db = Database()
    await db.initialize()
    
    try:
        column_map = {
            'public': 'public_log_channel_id',
            'private': 'private_log_channel_id',
            'report': 'report_log_channel_id'
        }
        
        column = column_map.get(log_type)
        if not column:
            return None
        
        cursor = await db.connection.execute(f'''
            SELECT {column} FROM guild_settings
            WHERE guild_id = ?
        ''', (guild.id,))
        
        row = await cursor.fetchone()
        
        if row and row[0]:
            channel = guild.get_channel(row[0])
            return channel
        
        return None
        
    except Exception as e:
        logger.error(f'ログチャンネル取得エラー: {e}')
        return None


def create_permission_embed(
    title: str,
    description: str,
    color: discord.Color = discord.Color.red()
) -> discord.Embed:
    """
    権限エラー用のEmbedを作成
    
    Args:
        title: タイトル
        description: 説明
        color: 色(デフォルトは赤)
        
    Returns:
        discord.Embed: 権限エラーEmbed
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=color
    )
    
    return embed
