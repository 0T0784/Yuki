# ==========================================
# ticket_auto_delete.py
# クローズチケット自動削除（1週間後）＋管理者ログ通知
# ==========================================

import discord
from discord.ext import commands, tasks
from database.db import get_connection
from datetime import datetime, timedelta
from cogs.admin.logs.log_embed import ticket_action_log_embed


class TicketAutoDelete(commands.Cog):
    """バックグラウンドでクローズ済チケットを自動削除"""

    def __init__(self, bot):
        self.bot = bot
        self.delete_closed_tickets.start()  # Bot起動時にタスク開始

    @tasks.loop(hours=1)
    async def delete_closed_tickets(self):
        """1時間ごとにDBをチェックして7日経過したクローズチャンネルを削除"""
        conn = get_connection()
        cur = conn.cursor()

        one_week_ago = datetime.utcnow() - timedelta(days=7)
        cur.execute("""
            SELECT guild_id, channel_id, user_id
            FROM ticket_logs
            WHERE status='CLOSED' AND closed_at <= ?
        """, (one_week_ago,))
        rows = cur.fetchall()
        conn.close()

        for guild_id, channel_id, user_id in rows:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            # 管理者ログ送信
            settings = get_connection().cursor().execute(
                "SELECT admin_log_channel FROM guild_settings WHERE guild_id=?",
                (guild_id,)
            ).fetchone()
            log_channel = guild.get_channel(settings[0]) if settings else None

            if log_channel:
                try:
                    member = guild.get_member(user_id)
                    await log_channel.send(
                        embed=ticket_action_log_embed(
                            action="クローズチケット自動削除",
                            user=member if member else discord.Object(id=user_id),
                            channel=channel,
                            reason="クローズから1週間経過"
                        )
                    )
                except:
                    pass

            # チャンネル削除
            try:
                await channel.delete()
            except:
                continue  # 削除失敗は無視

    @delete_closed_tickets.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()  # Bot起動完了まで待機


async def setup(bot):
    await bot.add_cog(TicketAutoDelete(bot))
