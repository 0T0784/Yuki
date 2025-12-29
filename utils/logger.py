"""
ロギングユーティリティ
Botの動作ログを管理します
"""

import logging
import os
from datetime import datetime


def setup_logger():
    """
    ロガーのセットアップを行う関数
    
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    # ログディレクトリの作成
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # ロガーの作成
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)
    
    # すでにハンドラーが設定されている場合はスキップ
    if logger.handlers:
        return logger
    
    # ファイルハンドラーの設定(日付ごとにログファイルを作成)
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(
        f'{log_dir}/bot_{today}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッターの設定
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラーをロガーに追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger():
    """
    既存のロガーインスタンスを取得する関数
    
    Returns:
        logging.Logger: ロガーインスタンス
    """
    return logging.getLogger('discord_bot')
