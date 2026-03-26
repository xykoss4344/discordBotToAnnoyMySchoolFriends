# 🤖 DebateBot3000 — Discord Troll Bot

A Discord bot powered by **Gemini AI** that argues with everything anyone says. It is always wrong. It will rant at you. It will personally roast you.

---

## Setup

### 1. Clone / open the project folder

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
Copy `.env.example` to `.env` and fill in your keys:
```
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

**Getting keys:**
- Discord token → https://discord.com/developers/applications → New App → Bot → Reset Token
- Gemini API key → https://aistudio.google.com/apikey

> ⚠️ Make sure to enable **Message Content Intent** in the Discord dev portal (Bot → Privileged Gateway Intents)

### 4. Run the bot
```bash
python bot.py
```

---

## Commands

| Command | Who | Description |
|---|---|---|
| `!debate <statement>` | Anyone | Force the bot to argue against your statement |
| `!argue <statement>` | Anyone | Alias for `!debate` |
| `!debate_mode <0.0–1.0>` | Admin | Set how often bot randomly hijacks messages (0 = off) |
| `!addtarget @user` | Admin | Make bot ALWAYS argue with a specific person |
| `!removetarget @user` | Admin | Remove them from the target list |
| `!ping` | Anyone | Check if bot is alive |

---

## Configuration (in `cogs/debater.py`)

| Setting | Default | Description |
|---|---|---|
| `PASSIVE_ENGAGE_CHANCE` | `0.25` | 25% chance bot randomly argues with any message |
| `COOLDOWN_SECONDS` | `5` | Seconds between debates per user |
| `ALLOWED_CHANNEL_IDS` | `[]` | Limit bot to specific channels (empty = all) |
| `TARGET_USER_IDS` | `[]` | Always debate these user IDs (empty = everyone) |

---

## How it works

1. Someone sends a message
2. Bot rolls the dice (or checks if they're a target)
3. Their message is sent to **Gemini** with a system prompt telling it to be a dramatic, unhinged contrarian
4. Gemini roasts them and explains why they're completely wrong
5. Bot replies 🔥
