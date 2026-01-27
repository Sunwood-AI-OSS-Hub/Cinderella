FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Node.jsをインストール（Claude Codeのnpmインストールに必要）
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Claude Codeをインストール
RUN npm install -g @anthropic-ai/claude-code

# 依存関係をインストール
RUN uv pip install --system fastapi uvicorn[standard] pydantic

# ソースコードをコピー
COPY . .

# ポートを公開
EXPOSE 8080

# サーバーを起動
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
