# ==========================================
# ticket_utils.py
# チケット共通処理
# ・権限設定
# ==========================================

import discord
from database.db import get_guild_settings


def build_ticket_overwrites(guild, user):
    """チケットチャンネルの閲覧権限"""
    settings = get_guild_settings(guild.id)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True),
    }

    if settings:
        role = guild.get_role(settings["admin_role_id"])
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True)

    return overwrites
