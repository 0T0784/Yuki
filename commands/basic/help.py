"""
/help コマンド
使用可能なコマンド一覧を表示します
"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import get_logger

logger = get_logger()


class Help(commands.Cog):
    """
    ヘルプコマンドのCog
    """
    
    def __init__(self, bot):
        """
        初期化
        
        Args:
            bot: Botインスタンス
        """
        self.bot = bot
    
    @app_commands.command(name="help", description="使用可能なコマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        """
        ヘルプコマンドのメイン処理
        ユーザーの権限に応じて表示内容を変更
        
        Args:
            interaction: インタラクション
        """
        # ユーザーの権限を確認
        is_admin = interaction.user.guild_permissions.administrator
        is_owner = interaction.user.id == interaction.guild.owner_id
        
        # Embedの作成
        embed = discord.Embed(
            title="📚 コマンド一覧",
            description="このBotで使用できるコマンドの一覧です。",
            color=discord.Color.blue()
        )
        
        # 基礎機能系コマンド(全員が使用可能)
        basic_commands = """
        `/info <タイプ> [ユーザー]` - 各種情報を表示
        `/help` - このヘルプを表示
        `/ping` - Botの応答速度を確認
        """
        embed.add_field(
            name="📊 基礎機能",
            value=basic_commands.strip(),
            inline=False
        )
        
        # アンケート系コマンド(全員が使用可能)
        questionnaire_commands = """
        `/questionnaire add <内容> <選択肢1> <選択肢2> [選択肢3]` - アンケートを作成
        `/questionnaire close [ID]` - アンケートを終了
        """
        embed.add_field(
            name="📋 アンケート機能",
            value=questionnaire_commands.strip(),
            inline=False
        )
        
        # レポート機能(全員が使用可能)
        report_commands = """
        `/report <対象> <内容> [チケット作成]` - 不適切な行動やバグを報告
        """
        embed.add_field(
            name="📝 レポート機能",
            value=report_commands.strip(),
            inline=False
        )
        
        # 管理者専用コマンド
        if is_admin or is_owner:
            admin_commands = """
            `/role <操作> <ロールタイプ>` - 管理者ロール・Botロールの管理
            """
            embed.add_field(
                name="👑 管理者設定",
                value=admin_commands.strip(),
                inline=False
            )
            
            moderation_commands = """
            `/timeout <ユーザー> <理由> <分数>` - ユーザーをタイムアウト
            `/untimeout <ユーザー> <理由>` - タイムアウトを解除
            `/kick <ユーザー> <理由>` - ユーザーをキック
            `/ban <ユーザー> <理由>` - ユーザーをBAN
            `/pin <メッセージID> [内容]` - メッセージを固定
            """
            embed.add_field(
                name="🛡️ モデレーション",
                value=moderation_commands.strip(),
                inline=False
            )
            
            ticket_commands = """
            `/ticket_panel <操作>` - チケットパネルの作成/削除
            `/ticket <操作> [作成者]` - チケットの管理(デバッグ用)
            """
            embed.add_field(
                name="🎫 チケットシステム",
                value=ticket_commands.strip(),
                inline=False
            )
            
            stats_commands = """
            `/stats <期間>` - サーバーの統計を表示
            `/stats_send <期間> <チャンネル>` - 定期的に統計を送信
            """
            embed.add_field(
                name="📈 統計機能",
                value=stats_commands.strip(),
                inline=False
            )
            
            log_commands = """
            `/logs <チャンネル> <ログタイプ>` - ログチャンネルの設定
            """
            embed.add_field(
                name="📋 ログ設定",
                value=log_commands.strip(),
                inline=False
            )
        
        # フッター
        if is_admin or is_owner:
            embed.set_footer(text="💡 管理者権限で全コマンドが表示されています")
        else:
            embed.set_footer(text="💡 一般ユーザーとして表示されています")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user.name}がヘルプを表示しました')


async def setup(bot):
    """
    Cogのセットアップ
    
    Args:
        bot: Botインスタンス
    """
    await bot.add_cog(Help(bot))
