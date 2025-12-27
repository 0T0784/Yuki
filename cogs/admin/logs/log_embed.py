# ==========================================
# log_embed.py
# 管理者ログ用Embed生成（完全統一版）
# ==========================================

import discord
from datetime import datetime


# ------------------------------------------
# 共通フォーマット
# ------------------------------------------

def _base_embed(title: str, color: discord.Color):
    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Admin Log System")
    return embed


# ------------------------------------------
# 処罰ログ（BAN / KICK / TIMEOUT / UN系）
# ------------------------------------------

def moderation_log_embed(
    *,
    action: str,
    target: discord.Member | discord.User,
    executor: discord.Member,
    reason: str,
):
    embed = _base_embed(
        title="🛡️ モデレーションログ",
        color=discord.Color.red()
    )

    embed.add_field(
        name="対象ユーザー",
        value=f"{target.mention}\n`{target.id}`",
        inline=False
    )

    embed.add_field(
        name="実行者",
        value=f"{executor.mention}\n`{executor.id}`",
        inline=False
    )

    embed.add_field(
        name="処理",
        value=action,
        inline=True
    )

    embed.add_field(
        name="理由",
        value=reason or "未指定",
        inline=True
    )

    return embed


# ------------------------------------------
# チケットパネル設置 / 削除ログ
# ------------------------------------------

def ticket_panel_log_embed(
    *,
    action: str,
    executor: discord.Member | None,
    channel: discord.TextChannel,
    message_id: int,
):
    embed = _base_embed(
        title="🎫 チケットパネル操作ログ",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="操作",
        value=action,
        inline=False
    )

    if executor:
        embed.add_field(
            name="実行者",
            value=f"{executor.mention}\n`{executor.id}`",
            inline=False
        )
    else:
        embed.add_field(
            name="実行者",
            value="不明（Bot / システム）",
            inline=False
        )

    embed.add_field(
        name="チャンネル",
        value=f"{channel.mention}\n`{channel.id}`",
        inline=False
    )

    embed.add_field(
        name="メッセージID",
        value=f"`{message_id}`",
        inline=False
    )

    return embed


# ------------------------------------------
# チケット操作ログ（作成 / クローズ）
# ------------------------------------------

def ticket_action_log_embed(
    *,
    action: str,
    user: discord.Member,
    channel: discord.TextChannel,
    reason: str | None = None,
):
    embed = _base_embed(
        title="📨 チケット操作ログ",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="操作",
        value=action,
        inline=False
    )

    embed.add_field(
        name="ユーザー",
        value=f"{user.mention}\n`{user.id}`",
        inline=False
    )

    embed.add_field(
        name="チャンネル",
        value=f"{channel.name}\n`{channel.id}`",
        inline=False
    )

    if reason:
        embed.add_field(
            name="理由",
            value=reason,
            inline=False
        )

    return embed
