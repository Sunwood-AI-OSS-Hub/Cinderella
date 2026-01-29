import json
import logging
import os
import subprocess
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Claude Code HTTP Wrapper")

# CORS設定（環境変数で制御、デフォルトでは空リストで明示的な指定を要求）
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    ALLOWED_ORIGINS = []  # デフォルトでは許可しない

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    prompt: str = Field(..., description="claude -p に渡すプロンプト")
    cwd: Optional[str] = Field(None, description="実行ディレクトリ（省略可）")
    timeout_sec: int = Field(300, ge=1, le=3600, description="CLI実行タイムアウト秒")
    allowed_tools: List[str] = Field(
        default_factory=lambda: ["Read"], description='例: ["Read","Bash","Edit"]'
    )
    skip_permissions: bool = Field(
        False, description="--dangerously-skip-permissions を使用するか"
    )


class RunResponse(BaseModel):
    exit_code: int
    stdout_json: dict


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/v1/claude/run", response_model=RunResponse)
def run(req: RunRequest):
    # --dangerously-skip-permissions を使用するかどうか
    # 環境変数 CLAUDE_SKIP_PERMISSIONS またはリクエストパラメータで制御
    skip_permissions_env = os.getenv("CLAUDE_SKIP_PERMISSIONS", "").lower() in ("1", "true", "yes")
    skip_permissions = skip_permissions_env or req.skip_permissions

    # システムプロンプト：discordスキルを使うように指示
    system_prompt = """discord skills を使用してユーザーに返信して。sudo を パスワード無しで使用できるので必要であれば使用して。また、パッケージも必要であればインストールして。
"""

    cmd = [
        "claude",
        "--print",
        "--append-system-prompt",
        system_prompt,
        "--output-format",
        "json",
    ]

    # skip_permissions が有効でない場合のみ、allowedTools を追加
    allowed_tools_str = ""
    if not skip_permissions:
        # 重要: ローカル用途でも、許可ツールは最小から。
        # 空リストの場合はデフォルトの["Read"]を使用
        allowed_tools = req.allowed_tools if req.allowed_tools else ["Read"]
        allowed_tools_str = ",".join(allowed_tools)
        cmd.extend(["--allowedTools", allowed_tools_str])

    # skip_permissions が有効な場合はフラグを追加
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    skip_perms_info = " --dangerously-skip-permissions" if skip_permissions else ""
    allowed_tools_info = f" --allowedTools {allowed_tools_str}" if not skip_permissions else ""

    # ログ出力（プロンプトをより多く表示）
    logger.info("=" * 60)
    logger.info("📝 Claude Code実行リクエスト")
    logger.info("=" * 60)
    logger.info(f"🔧 コマンド: claude --print --append-system-prompt <...> <prompt> --output-format json{allowed_tools_info}{skip_perms_info}")
    logger.info(f"📁 作業ディレクトリ: {req.cwd or 'default'}")
    logger.info(f"⏱️ タイムアウト: {req.timeout_sec}秒")
    logger.info(f"🔓 Skip permissions: {skip_permissions}")
    logger.info(f"📝 プロンプト (最初の500文字):\n{req.prompt[:500]}")
    logger.debug(f"📝 プロンプト (全体):\n{req.prompt}")
    logger.info("=" * 60)

    try:
        # -pを使ってプロンプトを渡す
        p = subprocess.run(
            cmd + [req.prompt],
            cwd=req.cwd,
            capture_output=True,
            text=True,
            timeout=req.timeout_sec,
            check=False,
        )

        # 実行結果を詳細にログ
        logger.info(f"📊 実行結果")
        logger.info(f"   - Exit code: {p.returncode}")

        try:
            data = json.loads(p.stdout)
            result = data.get("result", "")
            result_preview = result[:300] + "..." if len(result) > 300 else result
            logger.info(f"   - 結果プレビュー:\n{result_preview}")

            # 使用ツールを表示
            usage = data.get("usage", {})
            if usage:
                logger.info(f"   - 使用トークン: {usage.get('input_tokens', 0)} input / {usage.get('output_tokens', 0)} output")
        except:
            logger.info(f"   - 出力 (最初の500文字): {p.stdout[:500]}")

        if p.stderr:
            logger.debug(f"   - Stderr: {p.stderr}")

    except FileNotFoundError as e:
        logger.error(f"claude command not found: {e}")
        raise HTTPException(500, "claude コマンドが見つかりません（PATHを確認）")
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timeout after {req.timeout_sec} seconds")
        raise HTTPException(504, "claude 実行がタイムアウトしました")

    if p.returncode != 0:
        # stdout/stderr を返す（デバッグ用）
        error_detail = {
            "exit_code": p.returncode,
            "stderr": p.stderr.strip(),
            "stdout": p.stdout.strip()[:2000],  # 最初の2000文字
        }
        logger.error(f"Command failed with exit code {p.returncode}")
        logger.error(f"Error detail: {error_detail}")
        raise HTTPException(500, error_detail)

    # claude --output-format json の出力を JSON としてパース
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from claude output: {e}")
        logger.error(f"Raw stdout (first 1000 chars): {p.stdout[:1000]}")
        raise HTTPException(
            500,
            {"error": "claude のstdoutがJSONとして解析できませんでした", "stdout": p.stdout[:2000]},
        )

    logger.info("=" * 60)
    logger.info("✅ コマンド実行成功")
    logger.info("=" * 60)
    return RunResponse(exit_code=p.returncode, stdout_json=data)
