# ==========================================
# ticket_manage_view.py
# 担当 / クローズ管理
# ==========================================

import discord
from cogs.tickets.ticket_transcript import export_transcript


class TicketManageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👮 担当する", style=discord.ButtonStyle.success)
    async def assign(self, interaction, button):
        await interaction.channel.send(
            f"👮 担当者: {interaction.user.mention}"
        )
        await interaction.response.defer()

    @discord.ui.button(label="🔒 クローズ", style=discord.ButtonStyle.danger)
    async def close(self, interaction, button):
        await export_transcript(interaction.channel)
        await interaction.channel.delete()
