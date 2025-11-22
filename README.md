# Telegram YouTube View Bot

Advanced Telegram bot for YouTube view simulation with proxy management, user analytics, and comprehensive features.

## 🚀 Features

- **YouTube View Simulation**: Simulate views on YouTube videos using proxy rotation
- **Proxy Management**: Automatic proxy scraping, validation, and rotation
- **User Management**: Complete user database with statistics and history
- **Rate Limiting**: Built-in rate limiting per minute/hour/day
- **Analytics Engine**: Track events and user engagement
- **Notification System**: Send notifications to users
- **Task Scheduling**: Schedule recurring tasks
- **User Preferences**: Save user settings and preferences
- **Admin Controls**: Admin-only commands for bot management

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token
- Internet connection for proxy management

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/legendhkek/Yt.git
cd Yt
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Configure the bot:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

Or edit `config.py` to set your bot token and other settings.

4. Run the bot:
```bash
python3 bot.py
```

## 📁 File Structure

- `bot.py` - Main entry point (starts all components)
- `config.py` - Configuration management
- `utils.py` - Utility functions and helpers
- `features.py` - Advanced features (analytics, notifications, etc.)
- `test.py` - Test suite
- `setup.py` - Installation script
- `requirements.txt` - Python dependencies

## 🎯 Usage

### User Commands
- `/start` - Start the bot
- `/help` - Get help
- `/views` - Simulate views on a video
- `/stats` - View your statistics
- `/history` - View request history

### Admin Commands
- `/botstats` - View bot statistics
- `/proxies` - Manage proxy pool
- `/refresh_proxies` - Refresh proxy pool

## ⚙️ Configuration

Edit `config.py` or set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_token"
export ADMIN_IDS="123456789,987654321"
export RATE_LIMIT_VISITS_PER_MINUTE="15"
export PROXY_POOL_SIZE="150"
export MAX_WORKERS="75"
```

## 🔐 Security

- Rate limiting to prevent abuse
- Input validation and sanitization
- Secure token storage
- Admin-only commands

## 📊 Advanced Features

- **Analytics**: Track user events and engagement
- **Notifications**: Real-time notifications to users
- **Scheduling**: Automated tasks and maintenance
- **Caching**: LRU cache for performance
- **Logging**: Comprehensive logging system

## 🛠️ Development

Run tests:
```bash
python3 test.py
```

## 📝 License

Created by @LEGEND_BL

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## ⚠️ Disclaimer

This bot is for educational purposes only. Use responsibly and in accordance with YouTube's Terms of Service.
