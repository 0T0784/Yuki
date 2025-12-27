# ==========================================
# reason_select.py
# 処罰理由プルダウン
# ==========================================

import discord


REASONS = [
    "スパム行為",
    "荒らし行為",
    "暴言・ハラスメント",
    "規約違反",
    "その他"
]


class ReasonSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="処罰理由を選択してください",
            options=[discord.SelectOption(label=r) for r in REASONS],
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.reason = self.values[0]
        await interaction.response.defer()


class ReasonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.reason: str | None = None
        self.add_item(ReasonSelect())
