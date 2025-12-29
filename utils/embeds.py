"""
Embedヘルパーユーティリティ
統一されたデザインのEmbedを作成するヘルパー関数
"""

import discord
from datetime import datetime
from typing import Optional


def create_success_embed(
    title: str,
    description: str,
    fields: Optional[list] = None,
    footer: Optional[str] = None
) -> discord.Embed:
    """
    成功メッセージのEmbedを作成
    
    Args:
        title: タイトル
        description: 説明
        fields: フィールドのリスト(オプション)
        footer: フッター(オプション)
        
    Returns:
        discord.Embed: 成功Embed
    """
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed


def create_error_embed(
    title: str,
    description: str,
    fields: Optional[list] = None,
    footer: Optional[str] = None
) -> discord.Embed:
    """
    エラーメッセージのEmbedを作成
    
    Args:
        title: タイトル
        description: 説明
        fields: フィールドのリスト(オプション)
        footer: フッター(オプション)
        
    Returns:
        discord.Embed: エラーEmbed
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed


def create_warning_embed(
    title: str,
    description: str,
    fields: Optional[list] = None,
    footer: Optional[str] = None
) -> discord.Embed:
    """
    警告メッセージのEmbedを作成
    
    Args:
        title: タイトル
        description: 説明
        fields: フィールドのリスト(オプション)
        footer: フッター(オプション)
        
    Returns:
        discord.Embed: 警告Embed
    """
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=discord.Color.yellow(),
        timestamp=datetime.now()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed


def create_info_embed(
    title: str,
    description: str,
    fields: Optional[list] = None,
    footer: Optional[str] = None,
    thumbnail: Optional[str] = None
) -> discord.Embed:
    """
    情報メッセージのEmbedを作成
    
    Args:
        title: タイトル
        description: 説明
        fields: フィールドのリスト(オプション)
        footer: フッター(オプション)
        thumbnail: サムネイル画像URL(オプション)
        
    Returns:
        discord.Embed: 情報Embed
    """
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    return embed


def create_moderation_embed(
    action: str,
    moderator: discord.Member,
    target: discord.Member,
    reason: str,
    additional_fields: Optional[list] = None
) -> discord.Embed:
    """
    モデレーションアクション用のEmbedを作成
    
    Args:
        action: アクション名
        moderator: モデレーター
        target: 対象ユーザー
        reason: 理由
        additional_fields: 追加フィールド(オプション)
        
    Returns:
        discord.Embed: モデレーションEmbed
    """
    # アクションに応じて色とアイコンを変更
    action_config = {
        'timeout': {'color': discord.Color.orange(), 'icon': '⏱️'},
        'untimeout': {'color': discord.Color.green(), 'icon': '✅'},
        'kick': {'color': discord.Color.orange(), 'icon': '🥾'},
        'ban': {'color': discord.Color.red(), 'icon': '🔨'},
        'unban': {'color': discord.Color.green(), 'icon': '✅'}
    }
    
    config = action_config.get(action, {'color': discord.Color.blue(), 'icon': '🛡️'})
    
    embed = discord.Embed(
        title=f"{config['icon']} {action.upper()}実行",
        description=f"{target.mention}に対して{action}を実行しました。",
        color=config['color'],
        timestamp=datetime.now()
    )
    
    embed.add_field(name="対象ユーザー", value=target.mention, inline=True)
    embed.add_field(name="実行者", value=moderator.mention, inline=True)
    embed.add_field(name="理由", value=reason, inline=False)
    
    if additional_fields:
        for field in additional_fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    embed.set_footer(text=f"User ID: {target.id}")
    
    return embed


def create_log_embed(
    action: str,
    description: str,
    fields: Optional[list] = None,
    color: discord.Color = discord.Color.blue()
) -> discord.Embed:
    """
    ログ用のEmbedを作成
    
    Args:
        action: アクション名
        description: 説明
        fields: フィールドのリスト(オプション)
        color: 色(デフォルトは青)
        
    Returns:
        discord.Embed: ログEmbed
    """
    embed = discord.Embed(
        title=f"📝 {action}",
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', True)
            )
    
    return embed


def create_ticket_embed(
    ticket_id: int,
    creator: discord.Member,
    status: str = 'open'
) -> discord.Embed:
    """
    チケット用のEmbedを作成
    
    Args:
        ticket_id: チケットID
        creator: 作成者
        status: ステータス(デフォルトは'open')
        
    Returns:
        discord.Embed: チケットEmbed
    """
    color = discord.Color.green() if status == 'open' else discord.Color.greyple()
    icon = '🎫' if status == 'open' else '🔒'
    
    embed = discord.Embed(
        title=f"{icon} チケット #{ticket_id}",
        description=f"作成者: {creator.mention}",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="ステータス", value=status, inline=True)
    embed.add_field(name="作成者", value=creator.name, inline=True)
    
    if status == 'open':
        embed.add_field(
            name="説明",
            value="このチケットは管理者とあなたのみが閲覧できます。\n"
                  "ご用件を詳しくお書きください。",
            inline=False
        )
    
    embed.set_footer(text=f"Ticket ID: {ticket_id} | Creator ID: {creator.id}")
    
    return embed


def create_stats_embed(
    period: str,
    guild: discord.Guild,
    stats_data: dict
) -> discord.Embed:
    """
    統計用のEmbedを作成
    
    Args:
        period: 期間('week' または 'month')
        guild: サーバー
        stats_data: 統計データの辞書
        
    Returns:
        discord.Embed: 統計Embed
    """
    period_text = "週次" if period == "week" else "月次"
    
    embed = discord.Embed(
        title=f"📊 {guild.name}の{period_text}統計",
        description=f"{guild.name}の活動統計です。",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    # 統計データをフィールドとして追加
    for key, value in stats_data.items():
        embed.add_field(name=key, value=str(value), inline=True)
    
    embed.set_footer(text=f"{period_text}統計 | {guild.name}")
    
    return embed


def create_questionnaire_embed(
    questionnaire_id: str,
    content: str,
    options: list,
    creator: discord.Member,
    status: str = 'open'
) -> discord.Embed:
    """
    アンケート用のEmbedを作成
    
    Args:
        questionnaire_id: アンケートID
        content: アンケート内容
        options: 選択肢のリスト
        creator: 作成者
        status: ステータス(デフォルトは'open')
        
    Returns:
        discord.Embed: アンケートEmbed
    """
    color = discord.Color.blue() if status == 'open' else discord.Color.greyple()
    icon = '📋' if status == 'open' else '🔒'
    
    embed = discord.Embed(
        title=f"{icon} アンケート",
        description=content,
        color=color,
        timestamp=datetime.now()
    )
    
    # 選択肢を追加
    option_emojis = ['1️⃣', '2️⃣', '3️⃣']
    for i, option in enumerate(options):
        if i < len(option_emojis):
            embed.add_field(
                name=f"{option_emojis[i]} 選択肢{i+1}",
                value=option,
                inline=False
            )
    
    if status == 'open':
        embed.add_field(
            name="投票方法",
            value="リアクションをクリックして投票してください。",
            inline=False
        )
    
    embed.set_footer(text=f"ID: {questionnaire_id} | 作成者: {creator.name}")
    
    return embed