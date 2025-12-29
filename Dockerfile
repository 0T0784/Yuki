# Python 3.11のスリムイメージを使用
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 必要なシステムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# データベースディレクトリの作成
RUN mkdir -p data

# 環境変数の設定(本番環境では.envファイルまたはKoyebの環境変数で設定)
ENV PYTHONUNBUFFERED=1

# ポート8080を公開(Koyeb用)
EXPOSE 8080

# Botの起動
CMD ["python", "main.py"]