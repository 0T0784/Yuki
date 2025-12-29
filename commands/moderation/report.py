"""
/report コマンド
ユーザーの不適切な行動やBotのバグを報告
"""

import discord
from discord import app_commands
from discord.ext import commands

class Report(commands.Cog):
    @app_commands.command(name="report", description="不適切な行動やバグを報告")
    @app_commands.describe(
        target_type="報告対象",
        target="対象のユーザー(ユーザー報告の場合)",
        content="報告内容",
        create_ticket="チケットを作成するか"
    )
    @app_commands.choices(target_type=[
        app_commands.Choice(name="ユーザー", value="user"),
        app_commands.Choice(name="このBot", value="bot")
    ])
    async def report(
        self,
        interaction: discord.Interaction,
        target_type: app_commands.Choice[str],
        content: str,
        create_ticket: bool = False,
        target: discord.Member = None
    ):
        # レポートをデータベースに保存
        # 管理者ログチャンネルに送信
        # create_ticketがTrueの場合、チケットを作成
        pass

async def setup(bot):
    await bot.add_cog(Report(bot))