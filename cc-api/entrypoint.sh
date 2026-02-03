#!/bin/bash
set -e

# Git設定（環境変数から）
# 注意: このスクリプトはcinderellaユーザーで実行される必要があります
# セキュリティ: 値をログに出力しない（機密情報漏洩防止）
if [ -n "${GIT_USER_NAME:-}" ]; then
    git config --global user.name "${GIT_USER_NAME}"
    echo '✅ Git user.name configured'
fi

if [ -n "${GIT_USER_EMAIL:-}" ]; then
    git config --global user.email "${GIT_USER_EMAIL}"
    echo '✅ Git user.email configured'
fi

# 設定を確認（値はマスクして表示）
if [ -n "${GIT_USER_NAME:-}" ] || [ -n "${GIT_USER_EMAIL:-}" ]; then
    echo '📋 Git configuration:'
    git config --global --list | grep -E '^user\.' || true
fi

# サーバーを起動
exec "$@"
