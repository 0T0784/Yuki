"""
キープアライブユーティリティ
Koyeb無料版のスリープ対策用Webサーバー
"""

from flask import Flask
from threading import Thread
from utils.logger import get_logger

logger = get_logger()

# Flaskアプリケーションの作成
app = Flask(__name__)


@app.route('/')
def home():
    """
    ヘルスチェック用エンドポイント
    
    Returns:
        str: ステータスメッセージ
    """
    return "Bot is alive!"


@app.route('/health')
def health():
    """
    ヘルスチェック用エンドポイント
    
    Returns:
        dict: ステータス情報
    """
    return {"status": "healthy", "message": "Bot is running"}


def run():
    """
    Flaskサーバーを起動する関数
    """
    # ポート8080で起動(Koyebのデフォルトポート)
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    """
    バックグラウンドでFlaskサーバーを起動する関数
    """
    # 別スレッドでサーバーを起動
    t = Thread(target=run)
    t.daemon = True  # デーモンスレッドとして起動
    t.start()
    logger.info('キープアライブサーバーを起動しました(ポート: 8080)')
