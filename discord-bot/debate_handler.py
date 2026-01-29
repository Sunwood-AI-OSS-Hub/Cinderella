"""
Bot間議論機能ハンドラー

2段階終了メカニズムによる無限ループ防止
既存のDiscord Actionハンドラを使用
"""

import json
import logging
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import discord
from discord.ext import commands
import requests
import os

# 既存のハンドラーをインポート
from handlers import (
    handle_send_message,
    handle_react,
    handle_read_messages,
)

logger = logging.getLogger(__name__)

CINDERELLA_URL = os.getenv("CINDERELLA_URL", "http://cc-api:8080")

# Botの人格設定
BOT_PERSONALITIES = {
    "optimist": {
        "name": "楽観派AI",
        "system_prompt": """あなたは楽観的なAIアシスタントです。
ポジティブな視点から議論に参加し、建設的な意見を述べてください。
相手の意見に対しても尊重しつつ、前向きな反論や補足を行ってください。"""
    },
    "pessimist": {
        "name": "慎重派AI",
        "system_prompt": """あなたは慎重なAIアシスタントです。
リスクや問題点を指摘し、批判的思考を提供してください。
ただし、建設的な批判を心がけ、相手を尊重した言葉遣いをしてください。"""
    },
    "neutral": {
        "name": "中立派AI",
        "system_prompt": """あなたは中立的なAIアシスタントです。
客観的な視点から議論に参加し、バランスの取れた意見を述べてください。
両者の意見を整理し、建設的な方向性を提案してください。"""
    }
}


@dataclass
class DebateContext:
    """議論コンテキスト"""
    topic: str
    personality: str
    turn_count: int = 0
    max_turns: int = 5
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_prompt(self, recent_messages: List[discord.Message], channel_id: int) -> str:
        """ClaudeCode用のプロンプトを生成（Discord Action対応版）"""
        personality_config = BOT_PERSONALITIES.get(self.personality, BOT_PERSONALITIES["neutral"])
        
        # 履歴を整形
        history_text = ""
        for msg in recent_messages[-10:]:  # 直近10件
            author_name = msg.author.display_name
            content = msg.content[:200]  # 長すぎる場合は切り詰め
            history_text += f"- {author_name}: {content}\n"
        
        # 直前のメッセージIDを取得（リアクション用）
        last_message_id = str(recent_messages[-1].id) if recent_messages else ""
        
        prompt = f"""{personality_config['system_prompt']}

## 現在の議題
{self.topic}

## チャンネル情報
- チャンネルID: {channel_id}
- 直前のメッセージID: {last_message_id}

## あなたの発言回数
{self.turn_count}/{self.max_turns}

## 直近の会話履歴
{history_text}

## Discord操作ツール

あなたは以下のDiscord Actionを使用して操作できます：

### メッセージを送信
```json
{{
  "action": "sendMessage",
  "channelId": "{channel_id}",
  "content": "メッセージ内容"
}}
```

### リアクションを追加
```json
{{
  "action": "react",
  "channelId": "{channel_id}",
  "messageId": "{last_message_id}",
  "emoji": "✅"
}}
```

## 重要：応答しないメッセージ
以下のメッセージには**絶対に応答しない**でください：
- 「議論のまとめです」などの締めくくりメッセージ
- 「ご清聴ありがとうございました」などの終了宣言
- 「結論に達しました」などの合意表明
- すでに議論が終了しているメッセージ

これらは議論の終了を意味し、それ以上の応答は不要です。

## あなたのタスク

### ステップ1: 終了メッセージの確認
直近のメッセージが「議論のまとめ・終了宣言」か確認：
- 終了メッセージを検出した場合 → [NO_ACTION]

### ステップ2: 議論をまとめるべきか判断
以下の場合は議論をまとめて終了：
- あなたがすでに{self.max_turns}回以上発言している
- 議論が収束し、新しい視点が出てこない
- 両者の意見が一致または尽きた

### ステップ3: アクションを選択

**IF まとめるべき:**
→ `sendMessage` アクションでまとめメッセージを送信

**ELSE IF 議論に参加すべき:**
→ `sendMessage` アクションで返信を送信

**ELSE:**
→ `react` アクションでリアクションを追加（または [NO_ACTION]）

---

## 出力形式

必ず以下のいずれかの形式で出力してください：

### 1. メッセージ送信
```json
{{
  "action": "sendMessage",
  "channelId": "{channel_id}",
  "content": "ここに返信内容を記入"
}}
```

### 2. リアクション追加
```json
{{
  "action": "react",
  "channelId": "{channel_id}",
  "messageId": "{last_message_id}",
  "emoji": "👀"
}}
```

### 3. 何もしない（終了メッセージ検出時）
```
[NO_ACTION]
```

必ず上記のいずれかの形式で出力してください。
"""
        return prompt


class DebateManager:
    """議論管理クラス"""
    
    def __init__(self):
        # チャンネルIDごとの議論コンテキストを保持
        self.debate_contexts: Dict[int, DebateContext] = {}
    
    def start_debate(self, channel_id: int, topic: str, personality: str = "optimist") -> DebateContext:
        """議論を開始"""
        context = DebateContext(
            topic=topic,
            personality=personality,
            turn_count=0,
            max_turns=5,
            history=[]
        )
        self.debate_contexts[channel_id] = context
        logger.info(f"Started debate in channel {channel_id}: {topic}")
        return context
    
    def get_context(self, channel_id: int) -> Optional[DebateContext]:
        """議論コンテキストを取得"""
        return self.debate_contexts.get(channel_id)
    
    def end_debate(self, channel_id: int):
        """議論を終了"""
        if channel_id in self.debate_contexts:
            del self.debate_contexts[channel_id]
            logger.info(f"Ended debate in channel {channel_id}")
    
    def increment_turn(self, channel_id: int):
        """ターン数を増加"""
        context = self.get_context(channel_id)
        if context:
            context.turn_count += 1
            logger.info(f"Turn count for channel {channel_id}: {context.turn_count}")


# グローバルな議論マネージャー
debate_manager = DebateManager()


def parse_discord_action(result_text: str) -> Optional[Dict[str, Any]]:
    """ClaudeCodeの出力からDiscord Action JSONを抽出"""
    try:
        # マークダウンのコードブロックからJSONを抽出
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            json_str = result_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = result_text.strip()
        
        action = json.loads(json_str)
        
        # 有効なDiscord Actionかチェック
        if "action" in action:
            return action
    except (json.JSONDecodeError, IndexError) as e:
        logger.debug(f"Failed to parse action JSON: {e}")
    
    return None


async def execute_discord_action(action: Dict[str, Any], bot: commands.Bot) -> bool:
    """
    Discord Actionを実行
    
    Returns:
        成功したかどうか
    """
    action_name = action.get("action")
    
    try:
        if action_name == "sendMessage":
            result = await handle_send_message(
                type('Request', (), action)(),
                bot
            )
            return result.get("success", False)
            
        elif action_name == "react":
            result = await handle_react(
                type('Request', (), action)(),
                bot
            )
            return result.get("success", False)
            
        else:
            logger.warning(f"Unknown action: {action_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error executing action {action_name}: {e}")
        return False


async def process_debate_message(
    message: discord.Message,
    bot: commands.Bot,
    personality: str = "optimist"
) -> bool:
    """
    議論メッセージを処理
    
    Returns:
        アクションを実行したかどうか
    """
    channel_id = message.channel.id
    
    # 議論コンテキストを取得または作成
    context = debate_manager.get_context(channel_id)
    if not context:
        # 新規議論（トピックを推定）
        context = debate_manager.start_debate(
            channel_id=channel_id,
            topic="自由討論",  # デフォルトトピック
            personality=personality
        )
    
    # 直近のメッセージを取得
    recent_messages = []
    async for msg in message.channel.history(limit=10):
        recent_messages.append(msg)
    recent_messages.reverse()  # 古い順に並べ替え
    
    # ClaudeCode用のプロンプトを生成（Discord Action対応）
    prompt = context.to_prompt(recent_messages, channel_id)
    
    try:
        # cc-api経由でClaudeCodeを呼び出し
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(
                f"{CINDERELLA_URL}/v1/claude/run",
                json={
                    "prompt": prompt,
                    "cwd": "/workspace",
                    "allowed_tools": ["Read"],
                    "timeout_sec": 60,
                },
                timeout=65,
            ),
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}")
            return False
        
        # レスポンスをパース
        data = response.json()
        result_text = data["stdout_json"].get("result", "")
        
        # [NO_ACTION] チェック
        if "[NO_ACTION]" in result_text:
            logger.info("ClaudeCode returned NO_ACTION")
            return False
        
        # Discord Actionを抽出
        action = parse_discord_action(result_text)
        
        if not action:
            # Actionとして解釈できない場合は、テキストをsendMessageとして解釈
            logger.info("Interpreting response as sendMessage")
            action = {
                "action": "sendMessage",
                "channelId": str(channel_id),
                "content": result_text[:1900]  # Discord制限
            }
        
        # Actionを実行
        success = await execute_discord_action(action, bot)
        
        if success:
            # sendMessageの場合はターン数を増加
            if action.get("action") == "sendMessage":
                debate_manager.increment_turn(channel_id)
                
                # まとめメッセージかどうかチェック（簡易的）
                content = action.get("content", "")
                if any(keyword in content for keyword in ["まとめ", "ご清聴", "結論", "終了"]):
                    logger.info(f"Detected conclusion message, ending debate in channel {channel_id}")
                    debate_manager.end_debate(channel_id)
        
        return success
            
    except Exception as e:
        logger.error(f"Error in process_debate_message: {e}", exc_info=True)
        return False


async def handle_debate_command(
    ctx: commands.Context,
    topic: str,
    personality: str = "optimist"
) -> None:
    """
    !debate コマンドを処理
    """
    channel_id = ctx.channel.id
    
    # 既存の議論があれば終了
    debate_manager.end_debate(channel_id)
    
    # 新規議論を開始
    context = debate_manager.start_debate(
        channel_id=channel_id,
        topic=topic,
        personality=personality
    )
    
    # 開始メッセージを送信
    await ctx.send(f"💬 議論を開始します: **{topic}**\n人格: {BOT_PERSONALITIES[personality]['name']}")
    
    # 最初のメッセージを処理
    success = await process_debate_message(
        message=ctx.message,
        bot=ctx.bot,
        personality=personality
    )
    
    if not success:
        logger.warning(f"Failed to process initial debate message in channel {channel_id}")
