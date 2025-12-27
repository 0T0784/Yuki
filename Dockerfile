# ==========================================
# Dockerfile
# Bot用
# ==========================================
FROM python:3.12-slim

# 作業ディレクトリ
WORKDIR /app

# 依存関係コピー
COPY requirements.txt .

# パッケージインストール
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードコピー
COPY . .

# ポート設定（Flaskなどが必要な場合）
EXPOSE 8080

# CMDでBot起動
CMD ["python", "main.py"]
