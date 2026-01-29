# Debate Functionality

## Overview

The Discord bot includes a bot-to-bot debate feature that allows AI agents to engage in structured discussions on various topics.

## Architecture

### Components

1. **debate_handler.py** - Core debate logic
   - `DebateContext`: Stores debate state (topic, turn count, personality)
   - `DebateManager`: Manages active debates across channels
   - `process_debate_message()`: Handles incoming messages during debates

2. **bot.py** - Integration points
   - `!debate` command: Starts a new debate
   - `on_message` event: Triggers debate responses

### Personalities

The bot supports three personality types:

- **optimist** (楽観派AI): Positive and constructive
- **pessimist** (慎重派AI): Careful and critical
- **neutral** (中立派AI): Objective and balanced

## Usage

### Starting a Debate

```
!debate AIと仕事
!debate リモートワークの是非 --personality=optimist
!debate 気候変動対策 --personality=pessimist
```

### Debate Flow

1. User initiates debate with `!debate <topic>`
2. Bot responds with opening statement based on personality
3. Other bots in channel can respond to continue the debate
4. Debate ends after 5 turns per bot or when consensus is reached
5. Bot posts a summary message

## Implementation Details

### Message Flow

```
User: !debate AIと仕事
  ↓
Bot: 💬 議論を開始します: **AIと仕事**
     人格: 楽観派AI
  ↓
Bot: [AIと仕事についての最初の意見]
  ↓
Other Bot: [反論や追加の視点]
  ↓
Bot: [応答またはまとめ]
```

### Termination Conditions

Debates automatically end when:

1. Turn count reaches max_turns (default: 5)
2. Summary keywords detected: "まとめ", "ご清聴", "結論", "終了"
3. No new perspectives emerge

### Edge Cases Handled

1. **Bot's own messages**: Ignored to prevent loops
2. **Missing context**: Automatically creates new debate context
3. **API failures**: Graceful degradation with logging
4. **Invalid personalities**: Validation with error message

## API Integration

The debate feature integrates with:

1. **Claude Code API**: For generating responses
   - Endpoint: `http://cc-api:8080/v1/claude/run`
   - Tools: `["Read"]`
   - Timeout: 60 seconds

2. **Discord Actions**: For sending messages
   - `sendMessage`: Post responses
   - `react`: Add reactions

## Testing

Run debate tests:

```bash
cd discord-bot/tests
python test_debate_handler.py <channel_id> <guild_id>
```

## Future Enhancements

Potential improvements:

1. Custom personality configuration
2. Adjustable turn limits
3. Debate history persistence
4. Multi-language support
5. Voting mechanisms for debate conclusions
