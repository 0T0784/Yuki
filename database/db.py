# ==========================================
# db.py
# SQLite管理
# - モデレーションログ
# - サーバー設定
# - チケットログ
# ==========================================

import sqlite3
from datetime import datetime

DB_PATH = "data/bot.db"  # docker-compose.ymlでボリューム永続化

# -----------------------------
# DB接続
# -----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# ギルド設定
# -----------------------------
def create_guild_settings_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        admin_log_channel INTEGER,
        moderator_role_id INTEGER
    )
    """)
    conn.commit()
    conn.close()

def set_guild_settings(guild_id, admin_log_channel, moderator_role_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO guild_settings(guild_id, admin_log_channel, moderator_role_id)
    VALUES (?, ?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET
      admin_log_channel=excluded.admin_log_channel,
      moderator_role_id=excluded.moderator_role_id
    """, (guild_id, admin_log_channel, moderator_role_id))
    conn.commit()
    conn.close()

def get_guild_settings(guild_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,))
    row = cur.fetchone()
    conn.close()
    return row

# -----------------------------
# モデレーションログ
# -----------------------------
def create_mod_logs_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mod_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        target_id INTEGER,
        executor_id INTEGER,
        action TEXT,
        reason TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def add_mod_log(guild_id, target_id, executor_id, action, reason):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO mod_logs (guild_id, target_id, executor_id, action, reason)
    VALUES (?, ?, ?, ?, ?)
    """, (guild_id, target_id, executor_id, action, reason))
    conn.commit()
    conn.close()

# -----------------------------
# チケットログ
# -----------------------------
def create_ticket_logs_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ticket_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        channel_id INTEGER,
        user_id INTEGER,
        reason TEXT,
        status TEXT DEFAULT 'OPEN',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def add_ticket_log(guild_id, channel_id, user_id, reason):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO ticket_logs (guild_id, channel_id, user_id, reason)
    VALUES (?, ?, ?, ?)
    """, (guild_id, channel_id, user_id, reason))
    conn.commit()
    conn.close()

def mark_ticket_closed(channel_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE ticket_logs
    SET status='CLOSED', closed_at=CURRENT_TIMESTAMP
    WHERE channel_id=?
    """, (channel_id,))
    conn.commit()
    conn.close()

def get_closed_tickets_before(timestamp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT guild_id, channel_id, user_id
    FROM ticket_logs
    WHERE status='CLOSED' AND closed_at <= ?
    """, (timestamp,))
    rows = cur.fetchall()
    conn.close()
    return rows

# -----------------------------
# 初期化用関数（起動時に呼ぶ）
# -----------------------------
def initialize_db():
    create_guild_settings_table()
    create_mod_logs_table()
    create_ticket_logs_table()
