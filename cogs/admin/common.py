# ==========================================
# common.py
# 管理系 共通ユーティリティ
# ==========================================

import discord


async def send_dm(user: discord.User, title: str, message: str):
    """DM送信（失敗してもエラーにしない）"""
    try:
        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Color.blurple()
        )
        await user.send(embed=embed)
    except Exception:
        pass


def format_user(guild: discord.Guild, user: discord.abc.User):
    """ユーザー表示（オーナー👑対応）"""
    if guild.owner_id == user.id:
        return f"👑 {user} ({user.id})"
    return f"{user} ({user.id})"
