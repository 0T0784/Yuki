# ==========================================
# ticket_panel_view.py
# チケット作成ボタン
# ==========================================

import discord
from cogs.tickets.ticket_reason_view import TicketReasonView
from cogs.tickets.ticket_create import create_ticket


class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 チケットを作成", style=discord.ButtonStyle.primary)
    async def create(self, interaction, button):
        view = TicketReasonView()
        await interaction.response.send_message(
            "内容を選択してください",
            view=view,
            ephemeral=True,
        )
        await view.wait()

        channel = await create_ticket(
            interaction.guild,
            interaction.user,
            view.reason or "未指定",
        )

        await interaction.followup.send(
            f"✅ 作成しました: {channel.mention}",
            ephemeral=True,
        )
