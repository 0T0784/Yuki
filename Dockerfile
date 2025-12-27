# ==========================================
# Dockerfile
# Python 3.12 + 必要ライブラリ
# ==========================================
FROM python:3.12-slim

# 作業ディレクトリ
WORKDIR /app

# 必要なライブラリをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Botのソースをコピー
COPY . .

# ポート設定
EXPOSE 8080

# 起動コマンド
CMD ["python", "main.py"]
