import json
import os
import subprocess
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Local Claude Code HTTP Wrapper")


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
    allowed_tools_str = ",".join(req.allowed_tools) if req.allowed_tools else "Read"

    cmd = [
        "claude",
        "-p",
        req.prompt,
        "--output-format",
        "json",
        "--allowedTools",
        allowed_tools_str,
    ]

    try:
        p = subprocess.run(
            cmd,
            cwd=req.cwd,
            capture_output=True,
            text=True,
            timeout=req.timeout_sec,
            check=False,
        )
    except FileNotFoundError:
        raise HTTPException(500, "claude コマンドが見つかりません（PATHを確認）")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "claude 実行がタイムアウトしました")

    if p.returncode != 0:
        # stdout/stderr を返す（デバッグ用）
        raise HTTPException(
            500,
            {
                "exit_code": p.returncode,
                "stderr": p.stderr.strip(),
                "stdout": p.stdout.strip(),
            },
        )

    # claude --output-format json の出力を JSON としてパース
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            500,
            {"error": "claude のstdoutがJSONとして解析できませんでした", "stdout": p.stdout[:2000]},
        )

    return RunResponse(exit_code=p.returncode, stdout_json=data)
