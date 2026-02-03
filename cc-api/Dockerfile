FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Node.js（LTS版）、sudo、curl、gitをインストール
RUN apt-get update && \
    apt-get install -y curl sudo git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# cinderellaユーザーを作成し、sudoグループに追加
# 注意: Claude Codeが一部のツールでsudoを必要とする場合があるため、NOPASSWDを設定
# セキュリティ: 本番環境では必要最小限のコマンドのみを許可することを推奨
RUN useradd -m -s /bin/bash cinderella && \
    usermod -aG sudo cinderella && \
    echo 'cinderella ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/cinderella && \
    chmod 440 /etc/sudoers.d/cinderella

# Claude Codeをインストール（rootでインストール後、所有権を変更）
RUN npm install -g @anthropic-ai/claude-code

# 依存関係をインストール（レイヤー最適化のためまとめて実行）
RUN uv pip install --system \
    fastapi \
    uvicorn[standard] \
    pydantic \
    google-genai

# ソースコードをコピー（cc-apiディレクトリからコピー）
COPY server.py .
COPY entrypoint.sh /entrypoint.sh

# entrypoint.shを実行可能に
RUN chmod +x /entrypoint.sh

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

# entrypointを使用してサーバーを起動
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
