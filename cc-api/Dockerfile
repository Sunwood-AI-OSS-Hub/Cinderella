FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Node.js（LTS版）、sudo、curlをインストール
RUN apt-get update && \
    apt-get install -y curl sudo && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# cinderellaユーザーを作成し、sudoグループに追加（パスワードなしでsudo可能）
RUN useradd -m -s /bin/bash cinderella && \
    usermod -aG sudo cinderella && \
    echo 'cinderella ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/cinderella && \
    chmod 440 /etc/sudoers.d/cinderella

# Claude Codeをインストール（rootでインストール後、所有権を変更）
RUN npm install -g @anthropic-ai/claude-code

# 依存関係をインストール
RUN uv pip install --system fastapi uvicorn[standard] pydantic

# Google Genai SDK (agentic-vision-gemini スキル用)
RUN uv pip install --system google-genai

# ソースコードをコピー（cc-apiディレクトリからコピー）
COPY server.py .

# アプリケーションディレクトリの所有権をcinderellaに変更
RUN chown -R cinderella:cinderella /app

# workspace ディレクトリを作成し、cinderellaが使えるように設定
RUN mkdir -p /workspace && chown -R cinderella:cinderella /workspace

# .claudeディレクトリを準備
RUN mkdir -p /home/cinderella/.claude && \
    chown -R cinderella:cinderella /home/cinderella/.claude

# cinderellaユーザーに切り替え
USER cinderella

# ポートを公開
EXPOSE 8080

# サーバーを起動
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
