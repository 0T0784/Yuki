# ==========================================
# ticket_reason_view.py
# チケット理由プルダウン
# ==========================================

import discord

REASONS = ["質問", "バグ報告", "通報", "要望", "その他"]


class TicketReasonSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="チケットの内容を選択",
            options=[discord.SelectOption(label=r) for r in REASONS],
        )

    async def callback(self, interaction):
        self.view.reason = self.values[0]
        await interaction.response.defer()


class TicketReasonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.reason = None
        self.add_item(TicketReasonSelect())
