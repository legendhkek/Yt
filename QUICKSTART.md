# Quick Start Guide

Get your Telegram YouTube View Bot running in 3 minutes!

## Step 1: Get a Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Configure the Bot

Set your bot token as an environment variable:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your token
nano .env
```

## Step 3: Install Dependencies

```bash
pip3 install -r requirements.txt
```

## Step 4: Start the Bot

**Option A: Using the startup script (Easy)**
```bash
./start.sh
```

**Option B: Direct Python execution**
```bash
python3 bot.py
```

## Step 5: Use the Bot

1. Open Telegram and search for your bot
2. Send `/start` to begin
3. Use `/views` to simulate views on a YouTube video
4. Follow the prompts to enter:
   - YouTube video URL
   - Number of views (1-1000)
   - View duration (5-3600 seconds)

## Commands

### User Commands
- `/start` - Initialize the bot
- `/help` - Show help message
- `/views` - Start view simulation
- `/stats` - Show your statistics
- `/history` - View request history

### Admin Commands (set ADMIN_IDS in config)
- `/botstats` - Show bot statistics
- `/proxies` - View proxy pool status
- `/refresh_proxies` - Refresh proxy pool

## Troubleshooting

### Bot doesn't start
- Check your bot token is correct
- Ensure all dependencies are installed: `pip3 install -r requirements.txt`
- Check Python version: `python3 --version` (need 3.8+)

### No proxies available
- The bot will automatically scrape proxies on first run
- Use `/refresh_proxies` command (admin only) to manually refresh
- Check your internet connection

### Rate limit errors
Default limits:
- 15 views per minute
- 150 views per hour
- 1000 views per day

Adjust in `config.py` if needed.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore advanced features in `features.py`
- Customize configuration in `config.py`
- Run tests: `python3 test.py`

## Support

Created by @LEGEND_BL

For issues, check the logs in `telegram_bot.log`
