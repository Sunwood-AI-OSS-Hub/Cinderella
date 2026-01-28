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

# CORS設定（環境変数で制御）
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

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


class RunResponse(BaseModel):
    exit_code: int
    stdout_json: dict


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/v1/claude/run", response_model=RunResponse)
def run(req: RunRequest):
    # 重要: ローカル用途でも、許可ツールは最小から。
    # 空リストの場合はデフォルトの["Read"]を使用
    allowed_tools = req.allowed_tools if req.allowed_tools else ["Read"]
    allowed_tools_str = ",".join(allowed_tools)

    cmd = [
        "claude",
        "-p",
        req.prompt,
        "--output-format",
        "json",
        "--allowedTools",
        allowed_tools_str,
    ]

    logger.info(f"Executing command: claude -p [REDACTED] --output-format json --allowedTools {allowed_tools_str}")
    logger.info(f"Working directory: {req.cwd or 'default'}")
    logger.info(f"Timeout: {req.timeout_sec} seconds")
    logger.debug(f"Prompt (first 100 chars): {req.prompt[:100]}")

    try:
        p = subprocess.run(
            cmd,
            cwd=req.cwd,
            capture_output=True,
            text=True,
            timeout=req.timeout_sec,
            check=False,
        )
        logger.debug(f"Command exit code: {p.returncode}")
        logger.debug(f"Command stdout (first 500 chars): {p.stdout[:500]}")
        if p.stderr:
            logger.debug(f"Command stderr: {p.stderr}")
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

    logger.info("Command executed successfully")
    return RunResponse(exit_code=p.returncode, stdout_json=data)
