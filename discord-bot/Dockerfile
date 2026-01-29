FROM python:3.12-slim

WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY bot.py .

# 実行
CMD ["python", "bot.py"]
