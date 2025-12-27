# ==========================================
# permissions.py
# 管理者権限チェック用
# ==========================================

from discord import Interaction
from discord.app_commands import check
from utils import db

def has_admin_role(interaction: Interaction) -> bool:
    """管理者か判定"""
    if interaction.user.guild_permissions.administrator:
        return True
    admin_role_id = db.get_admin_role(interaction.guild.id)
    if admin_role_id:
        return any(role.id == admin_role_id for role in interaction.user.roles)
    return False

def admin_only():
    """app_commands用デコレータ"""
    async def predicate(interaction: Interaction) -> bool:
        return has_admin_role(interaction)
    return check(predicate)
