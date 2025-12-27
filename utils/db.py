# ==========================================
# db.py
# サーバー設定用データベース (簡易的に辞書で管理)
# ==========================================

guild_admin_roles = {}  # {guild_id: role_id}

def set_admin_role(guild_id: int, role_id: int):
    """サーバーの管理者ロールを設定"""
    guild_admin_roles[guild_id] = role_id

def get_admin_role(guild_id: int) -> int | None:
    """サーバーの管理者ロールを取得"""
    return guild_admin_roles.get(guild_id)
