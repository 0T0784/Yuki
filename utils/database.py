"""
データベースユーティリティ
SQLiteデータベースを使用してBot情報を管理します
"""

import aiosqlite
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger()


class Database:
    """
    データベース管理クラス
    """
    
    def __init__(self):
        """
        データベースの初期化
        """
        self.db_path = 'data/bot_database.db'
        self.connection = None
    
    async def initialize(self):
        """
        データベースの初期化とテーブル作成
        """
        # データディレクトリの作成
        os.makedirs('data', exist_ok=True)
        
        # データベース接続
        self.connection = await aiosqlite.connect(self.db_path)
        
        # テーブルの作成
        await self._create_tables()
        
        logger.info('データベースの初期化が完了しました')
    
    async def _create_tables(self):
        """
        必要なテーブルを作成する内部関数
        """
        # サーバー設定テーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                admin_role_ids TEXT,
                bot_role_ids TEXT,
                public_log_channel_id INTEGER,
                private_log_channel_id INTEGER,
                report_log_channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ユーザー統計テーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                guild_id INTEGER,
                user_id INTEGER,
                message_count INTEGER DEFAULT 0,
                timeout_count INTEGER DEFAULT 0,
                kick_count INTEGER DEFAULT 0,
                ban_count INTEGER DEFAULT 0,
                ticket_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        # チケットテーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                creator_id INTEGER,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        ''')
        
        # アンケートテーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS questionnaires (
                questionnaire_id TEXT PRIMARY KEY,
                guild_id INTEGER,
                channel_id INTEGER,
                message_id INTEGER,
                creator_id INTEGER,
                content TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # レポートテーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                reporter_id INTEGER,
                target_type TEXT,
                target_id INTEGER,
                content TEXT,
                ticket_created BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 統計送信設定テーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS stats_schedule (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                period TEXT,
                last_sent TIMESTAMP
            )
        ''')
        
        # モデレーションログテーブル
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS moderation_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                moderator_id INTEGER,
                target_id INTEGER,
                action_type TEXT,
                reason TEXT,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self.connection.commit()
    
    async def initialize_guild(self, guild_id: int):
        """
        新しいサーバーのデータを初期化
        
        Args:
            guild_id: サーバーID
        """
        await self.connection.execute('''
            INSERT OR IGNORE INTO guild_settings (guild_id)
            VALUES (?)
        ''', (guild_id,))
        await self.connection.commit()
    
    async def increment_user_message_count(self, guild_id: int, user_id: int):
        """
        ユーザーのメッセージカウントを増やす
        
        Args:
            guild_id: サーバーID
            user_id: ユーザーID
        """
        await self.connection.execute('''
            INSERT INTO user_stats (guild_id, user_id, message_count, last_updated)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                message_count = message_count + 1,
                last_updated = ?
        ''', (guild_id, user_id, datetime.now(), datetime.now()))
        await self.connection.commit()
    
    async def get_user_stats(self, guild_id: int, user_id: int):
        """
        ユーザーの統計情報を取得
        
        Args:
            guild_id: サーバーID
            user_id: ユーザーID
            
        Returns:
            dict: ユーザーの統計情報
        """
        cursor = await self.connection.execute('''
            SELECT message_count, timeout_count, kick_count, ban_count, ticket_count
            FROM user_stats
            WHERE guild_id = ? AND user_id = ?
        ''', (guild_id, user_id))
        
        row = await cursor.fetchone()
        
        if row:
            return {
                'message_count': row[0],
                'timeout_count': row[1],
                'kick_count': row[2],
                'ban_count': row[3],
                'ticket_count': row[4]
            }
        else:
            return {
                'message_count': 0,
                'timeout_count': 0,
                'kick_count': 0,
                'ban_count': 0,
                'ticket_count': 0
            }
    
    async def close(self):
        """
        データベース接続を閉じる
        """
        if self.connection:
            await self.connection.close()