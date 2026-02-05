#!/bin/bash
set -e

# Git設定（環境変数から）
if [ -n "$GIT_USER_NAME" ]; then
    git config --global user.name "$GIT_USER_NAME"
    echo "✅ Git user.name set to: $GIT_USER_NAME"
fi

if [ -n "$GIT_USER_EMAIL" ]; then
    git config --global user.email "$GIT_USER_EMAIL"
    echo "✅ Git user.email set to: $GIT_USER_EMAIL"
fi

# 設定を確認
if [ -n "$GIT_USER_NAME" ] || [ -n "$GIT_USER_EMAIL" ]; then
    echo "📋 Git configuration:"
    git config --global --list | grep user || true
fi

# サーバーを起動
exec "$@"
