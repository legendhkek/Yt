#!/usr/bin/env python3
"""
BOT CONFIGURATION
Centralized configuration management for the Telegram bot.

Author: Manus Bot Development
Version: 2.0
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8057347461:AAHa2nmOZQIMf82V3gmpmcoWfyITsbD8-Sc")
BOT_NAME = os.getenv("BOT_NAME", "YouTube View Bot")
BOT_VERSION = "2.0"
BOT_AUTHOR = "@LEGEND_BL"

# Database Configuration
DATABASE_FILE = os.getenv("DATABASE_FILE", "telegram_bot.db")
ANALYTICS_DB = os.getenv("ANALYTICS_DB", "analytics.db")
PREFERENCES_DB = os.getenv("PREFERENCES_DB", "user_preferences.db")

# Cache Configuration
PROXY_CACHE_FILE = os.getenv("PROXY_CACHE_FILE", "proxy_cache.json")
USERS_CACHE_FILE = os.getenv("USERS_CACHE_FILE", "users_cache.json")
STATS_FILE = os.getenv("STATS_FILE", "bot_stats.json")

# Logging Configuration
LOG_FILE = os.getenv("LOG_FILE", "telegram_bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Admin Configuration
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
OWNER_ID = int(os.getenv("OWNER_ID", "5652614329"))
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID", "0")) if os.getenv("SUPPORT_CHAT_ID") else None

# ============================================================================
# YOUTUBE VIEW CONFIGURATION
# ============================================================================

# View time constraints
MIN_VIEW_TIME = int(os.getenv("MIN_VIEW_TIME", "5"))
MAX_VIEW_TIME = int(os.getenv("MAX_VIEW_TIME", "3600"))
DEFAULT_VIEW_TIME = int(os.getenv("DEFAULT_VIEW_TIME", "30"))

# View limits
MIN_VIEW_COUNT = int(os.getenv("MIN_VIEW_COUNT", "1"))
MAX_VIEW_COUNT = int(os.getenv("MAX_VIEW_COUNT", "1000"))
DEFAULT_VIEW_COUNT = int(os.getenv("DEFAULT_VIEW_COUNT", "100"))

# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

RATE_LIMIT_VISITS_PER_MINUTE = int(os.getenv("RATE_LIMIT_VISITS_PER_MINUTE", "15"))
RATE_LIMIT_VISITS_PER_HOUR = int(os.getenv("RATE_LIMIT_VISITS_PER_HOUR", "150"))
RATE_LIMIT_VISITS_PER_DAY = int(os.getenv("RATE_LIMIT_VISITS_PER_DAY", "1000"))

# ============================================================================
# PROXY CONFIGURATION
# ============================================================================

PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", "12"))
PROXY_VALIDATION_INTERVAL = int(os.getenv("PROXY_VALIDATION_INTERVAL", "3600"))
MAX_PROXY_FAILURES = int(os.getenv("MAX_PROXY_FAILURES", "5"))
PROXY_POOL_SIZE = int(os.getenv("PROXY_POOL_SIZE", "150"))
MIN_PROXY_POOL_SIZE = int(os.getenv("MIN_PROXY_POOL_SIZE", "50"))

PROXY_SOURCES = [
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
]

# ============================================================================
# THREADING CONFIGURATION
# ============================================================================

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "75"))
THREAD_POOL_TIMEOUT = int(os.getenv("THREAD_POOL_TIMEOUT", "45"))

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "3600"))
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "1000"))

# ============================================================================
# FEATURE FLAGS
# ============================================================================

ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
ENABLE_SCHEDULING = os.getenv("ENABLE_SCHEDULING", "true").lower() == "true"
ENABLE_PLUGINS = os.getenv("ENABLE_PLUGINS", "false").lower() == "true"
ENABLE_PREMIUM = os.getenv("ENABLE_PREMIUM", "false").lower() == "true"

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
API_RETRY_DELAY = int(os.getenv("API_RETRY_DELAY", "2"))

# ============================================================================
# CONVERSATION STATES
# ============================================================================

WAITING_FOR_URL = 1
WAITING_FOR_VIEWS = 2
WAITING_FOR_TIME = 3
WAITING_FOR_CONFIRMATION = 4
WAITING_FOR_PROXY_SOURCE = 5

# ============================================================================
# MESSAGES AND STRINGS
# ============================================================================

MESSAGES = {
    "welcome": (
        "🎬 *Welcome to YouTube View Bot!*\n\n"
        "This bot helps you simulate views on YouTube videos.\n\n"
        "*Available Commands:*\n"
        "🔗 /start - Start the bot\n"
        "📊 /stats - View your statistics\n"
        "🎥 /views - Simulate views on a video\n"
        "📋 /history - View your request history\n"
        "ℹ️ /help - Get help\n"
        "⚙️ /settings - Adjust settings\n"
    ),
    "help": (
        "📚 *Help Guide*\n\n"
        "*How to use this bot:*\n\n"
        "1️⃣ Send a YouTube video link\n"
        "2️⃣ Specify the number of views you want\n"
        "3️⃣ Choose the view duration\n"
        "4️⃣ Confirm and start the process\n\n"
        "*Supported URL formats:*\n"
        "• https://www.youtube.com/watch?v=VIDEO_ID\n"
        "• https://youtu.be/VIDEO_ID\n"
        "• https://www.youtube.com/embed/VIDEO_ID\n"
    ),
    "invalid_url": "❌ Invalid YouTube URL. Please send a valid YouTube link.",
    "invalid_number": "❌ Invalid number. Please enter a valid number.",
    "error": "❌ An error occurred. Please try again later.",
    "success": "✅ Operation completed successfully.",
    "processing": "⏳ Processing your request...\nThis may take a few moments.",
}

# ============================================================================
# CONFIGURATION CLASS
# ============================================================================

class Config:
    """Configuration management class"""
    
    _instance = None
    _config_file = "bot_config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize configuration"""
        if self._initialized:
            return
        
        self._initialized = True
        self.load_from_file()
    
    def load_from_file(self):
        """Load configuration from file"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r') as f:
                    config_data = json.load(f)
                    for key, value in config_data.items():
                        setattr(self, key, value)
            except Exception as e:
                print(f"Error loading config file: {e}")
    
    def save_to_file(self):
        """Save configuration to file"""
        try:
            config_data = {
                'BOT_TOKEN': BOT_TOKEN,
                'BOT_NAME': BOT_NAME,
                'BOT_VERSION': BOT_VERSION,
                'ADMIN_IDS': ADMIN_IDS,
                'RATE_LIMIT_VISITS_PER_MINUTE': RATE_LIMIT_VISITS_PER_MINUTE,
                'RATE_LIMIT_VISITS_PER_HOUR': RATE_LIMIT_VISITS_PER_HOUR,
                'RATE_LIMIT_VISITS_PER_DAY': RATE_LIMIT_VISITS_PER_DAY,
                'PROXY_POOL_SIZE': PROXY_POOL_SIZE,
                'MAX_WORKERS': MAX_WORKERS,
                'ENABLE_ANALYTICS': ENABLE_ANALYTICS,
                'ENABLE_NOTIFICATIONS': ENABLE_NOTIFICATIONS,
                'ENABLE_SCHEDULING': ENABLE_SCHEDULING,
                'ENABLE_PLUGINS': ENABLE_PLUGINS,
                'ENABLE_PREMIUM': ENABLE_PREMIUM,
            }
            
            with open(self._config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self, key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'BOT_TOKEN': BOT_TOKEN,
            'BOT_NAME': BOT_NAME,
            'BOT_VERSION': BOT_VERSION,
            'DATABASE_FILE': DATABASE_FILE,
            'LOG_FILE': LOG_FILE,
            'LOG_LEVEL': LOG_LEVEL,
            'ADMIN_IDS': ADMIN_IDS,
            'MIN_VIEW_TIME': MIN_VIEW_TIME,
            'MAX_VIEW_TIME': MAX_VIEW_TIME,
            'DEFAULT_VIEW_TIME': DEFAULT_VIEW_TIME,
            'RATE_LIMIT_VISITS_PER_MINUTE': RATE_LIMIT_VISITS_PER_MINUTE,
            'RATE_LIMIT_VISITS_PER_HOUR': RATE_LIMIT_VISITS_PER_HOUR,
            'RATE_LIMIT_VISITS_PER_DAY': RATE_LIMIT_VISITS_PER_DAY,
            'PROXY_TIMEOUT': PROXY_TIMEOUT,
            'PROXY_POOL_SIZE': PROXY_POOL_SIZE,
            'MAX_WORKERS': MAX_WORKERS,
            'CACHE_EXPIRY': CACHE_EXPIRY,
            'MAX_CACHE_SIZE': MAX_CACHE_SIZE,
            'ENABLE_ANALYTICS': ENABLE_ANALYTICS,
            'ENABLE_NOTIFICATIONS': ENABLE_NOTIFICATIONS,
            'ENABLE_SCHEDULING': ENABLE_SCHEDULING,
            'ENABLE_PLUGINS': ENABLE_PLUGINS,
            'ENABLE_PREMIUM': ENABLE_PREMIUM,
        }

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_config() -> Tuple[bool, str]:
    """Validate configuration"""
    errors = []
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("BOT_TOKEN not configured")
    
    if MIN_VIEW_TIME < 1:
        errors.append("MIN_VIEW_TIME must be at least 1")
    
    if MAX_VIEW_TIME < MIN_VIEW_TIME:
        errors.append("MAX_VIEW_TIME must be greater than MIN_VIEW_TIME")
    
    if PROXY_POOL_SIZE < MIN_PROXY_POOL_SIZE:
        errors.append(f"PROXY_POOL_SIZE must be at least {MIN_PROXY_POOL_SIZE}")
    
    if MAX_WORKERS < 1:
        errors.append("MAX_WORKERS must be at least 1")
    
    if errors:
        return False, "\n".join(errors)
    
    return True, "Configuration is valid"

# ============================================================================
# EXPORT ALL CONFIGURATION
# ============================================================================

__all__ = [
    'BOT_TOKEN',
    'BOT_NAME',
    'BOT_VERSION',
    'DATABASE_FILE',
    'LOG_FILE',
    'LOG_LEVEL',
    'ADMIN_IDS',
    'OWNER_ID',
    'MIN_VIEW_TIME',
    'MAX_VIEW_TIME',
    'DEFAULT_VIEW_TIME',
    'RATE_LIMIT_VISITS_PER_MINUTE',
    'RATE_LIMIT_VISITS_PER_HOUR',
    'RATE_LIMIT_VISITS_PER_DAY',
    'PROXY_TIMEOUT',
    'PROXY_POOL_SIZE',
    'MAX_WORKERS',
    'CACHE_EXPIRY',
    'MAX_CACHE_SIZE',
    'ENABLE_ANALYTICS',
    'ENABLE_NOTIFICATIONS',
    'ENABLE_SCHEDULING',
    'ENABLE_PLUGINS',
    'ENABLE_PREMIUM',
    'MESSAGES',
    'Config',
    'validate_config',
]
