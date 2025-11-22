#!/bin/bash
# Telegram YouTube View Bot - Startup Script
# This script starts the bot and all its components

echo "=========================================="
echo "  Telegram YouTube View Bot"
echo "  Version: 2.0 Advanced"
echo "  Author: @LEGEND_BL"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import telegram" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -q -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Check for bot token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo ""
    echo "⚠️  TELEGRAM_BOT_TOKEN environment variable not set"
    echo "   Please set it before running the bot:"
    echo "   export TELEGRAM_BOT_TOKEN='your_token_here'"
    echo ""
    echo "   Or the bot will use the token from config.py"
fi

echo ""
echo "🚀 Starting bot..."
echo "   Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Run the bot
python3 bot.py

# Exit code
EXIT_CODE=$?
echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Bot stopped gracefully"
else
    echo "❌ Bot stopped with error code: $EXIT_CODE"
fi
echo "=========================================="
exit $EXIT_CODE
