# ==========================================
# ticket_create.py
# チケットチャンネル生成処理
# ==========================================

import discord
from cogs.tickets.ticket_utils import build_ticket_overwrites
from cogs.tickets.ticket_manage_view import TicketManageView
from database.db import add_ticket_log


async def create_ticket(guild, user, reason):
    overwrites = build_ticket_overwrites(guild, user)

    channel = await guild.create_text_channel(
        name=f"ticket-{user.name}",
        overwrites=overwrites,
    )

    embed = discord.Embed(
        title="🎫 サポートチケット",
        description=f"理由: **{reason}**\n管理者が対応します。",
        color=discord.Color.blurple(),
    )

    await channel.send(embed=embed, view=TicketManageView())
    add_ticket_log(guild.id, channel.id, user.id, reason, "OPEN")
    return channel
