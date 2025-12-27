# ==========================================
# Dockerfile
# Discord Bot用（Koyeb対応）
# ==========================================

# Python 3.11 ベース
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存ライブラリのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Pythonライブラリインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードコピー
COPY . .

# 環境変数はKoyeb側で設定（.env使用可能）
# CMDでBot起動
CMD ["python", "-u", "main.py"]
