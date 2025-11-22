#!/usr/bin/env python3
"""
TELEGRAM BOT WITH YOUTUBE VIEW SIMULATION
Advanced Telegram bot with YouTube view simulation, proxy management,
user management, database integration, and comprehensive features.

Author: @LEGEND_BL
Version: 2.0 Advanced
Main Entry Point - Starts all bot components
"""

import os
import sys
import json
import time
import random
import threading
import sqlite3
import logging
import hashlib
import uuid
import pickle
import traceback
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from urllib.parse import urlparse, parse_qs, quote
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from collections import defaultdict, deque, OrderedDict
from functools import wraps
import re
import base64

# Import bot modules (before logging to avoid premature logging)
MODULES_LOADED = False
try:
    from utils import (
        LRUCache, Validator, Formatter, SecurityUtils,
        retry_on_failure, rate_limit, timed_cache
    )
    from features import (
        AnalyticsEngine, NotificationManager, TaskScheduler,
        PluginManager, UserPreferences, CommandRegistry
    )
    from config import (
        BOT_TOKEN, BOT_NAME, BOT_VERSION, DATABASE_FILE, 
        LOG_FILE, ADMIN_IDS, OWNER_ID, MIN_VIEW_TIME,
        MAX_VIEW_TIME, DEFAULT_VIEW_TIME, RATE_LIMIT_VISITS_PER_MINUTE,
        RATE_LIMIT_VISITS_PER_HOUR, RATE_LIMIT_VISITS_PER_DAY,
        PROXY_TIMEOUT, PROXY_POOL_SIZE, MAX_WORKERS,
        MESSAGES, Config, validate_config
    )
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    _import_error = str(e)

# Third-party imports
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import aiohttp
import asyncio
from bs4 import BeautifulSoup

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, 
    ConversationHandler, CallbackQueryHandler, CallbackContext
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError, BadRequest, Forbidden

# ============================================================================
# CONFIGURATION AND CONSTANTS (Loaded from config.py)
# ============================================================================

# Load configuration - use defaults if config module not available
if not MODULES_LOADED:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    DATABASE_FILE = "telegram_bot.db"
    LOG_FILE = "telegram_bot.log"
    ADMIN_IDS = []
    OWNER_ID = 0
    MIN_VIEW_TIME = 5
    MAX_VIEW_TIME = 3600
    DEFAULT_VIEW_TIME = 30
    RATE_LIMIT_VISITS_PER_MINUTE = 15
    RATE_LIMIT_VISITS_PER_HOUR = 150
    RATE_LIMIT_VISITS_PER_DAY = 1000
    PROXY_TIMEOUT = 12
    PROXY_POOL_SIZE = 150
    MAX_WORKERS = 75

# Additional constants
PROXY_CACHE_FILE = "proxy_cache.json"
USERS_CACHE_FILE = "users_cache.json"
STATS_FILE = "bot_stats.json"
PROXY_VALIDATION_INTERVAL = 3600
MAX_PROXY_FAILURES = 5
MIN_PROXY_POOL_SIZE = 50
THREAD_POOL_TIMEOUT = 45
CACHE_EXPIRY = 3600
MAX_CACHE_SIZE = 1000

# Conversation states
WAITING_FOR_URL = 1
WAITING_FOR_VIEWS = 2
WAITING_FOR_TIME = 3
WAITING_FOR_CONFIRMATION = 4
WAITING_FOR_PROXY_SOURCE = 5

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging():
    """Configure comprehensive logging system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Log module loading status after logging is configured
if MODULES_LOADED:
    logger.info("✅ All bot modules loaded successfully")
else:
    logger.warning(f"⚠️ Could not import some modules: {_import_error}. Running in standalone mode.")

# ============================================================================
# USER AGENT ROTATION SYSTEM
# ============================================================================

class UserAgentRotator:
    """Advanced user agent rotation to avoid detection"""
    
    DESKTOP_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    
    MOBILE_AGENTS = [
        "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    ]
    
    TABLET_AGENTS = [
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",
    ]
    
    def __init__(self):
        """Initialize user agent rotator"""
        self.all_agents = self.DESKTOP_AGENTS + self.MOBILE_AGENTS + self.TABLET_AGENTS
        self.device_types = ["desktop", "mobile", "tablet"]
        self.last_agent = None
    
    def get_random_agent(self, device_type: Optional[str] = None) -> Tuple[str, str]:
        """Get random user agent and device type"""
        if device_type is None:
            device_type = random.choice(self.device_types)
        
        if device_type == "mobile":
            agents = self.MOBILE_AGENTS
        elif device_type == "tablet":
            agents = self.TABLET_AGENTS
        else:
            agents = self.DESKTOP_AGENTS
        
        agent = random.choice(agents)
        self.last_agent = agent
        return agent, device_type
    
    def get_headers(self, device_type: Optional[str] = None) -> Dict[str, str]:
        """Generate realistic headers with random user agent"""
        agent, device = self.get_random_agent(device_type)
        
        headers = {
            "User-Agent": agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.8",
                "de-DE,de;q=0.9",
                "fr-FR,fr;q=0.9",
                "es-ES,es;q=0.9",
                "it-IT,it;q=0.9",
                "ja-JP,ja;q=0.9",
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
            "Pragma": "no-cache",
        }
        
        return headers

# ============================================================================
# PROXY MANAGEMENT SYSTEM
# ============================================================================

class ProxyManager:
    """Advanced proxy management with validation and rotation"""
    
    PROXY_SOURCES = [
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://www.proxy-list.download/api/v1/get?type=socks4",
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    ]
    
    def __init__(self):
        """Initialize proxy manager"""
        self.proxies: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.last_validation = 0
        self.validation_interval = PROXY_VALIDATION_INTERVAL
        self.user_agent_rotator = UserAgentRotator()
        self.failed_proxies = set()
    
    def load_from_cache(self) -> bool:
        """Load proxies from cache file"""
        try:
            if os.path.exists(PROXY_CACHE_FILE):
                with open(PROXY_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self.proxies = data.get('proxies', [])
                    logger.info(f"Loaded {len(self.proxies)} proxies from cache")
                    return len(self.proxies) > 0
        except Exception as e:
            logger.error(f"Error loading proxy cache: {e}")
        return False
    
    def save_to_cache(self):
        """Save proxies to cache file"""
        try:
            with open(PROXY_CACHE_FILE, 'w') as f:
                json.dump({
                    'proxies': self.proxies,
                    'timestamp': time.time(),
                    'count': len(self.proxies)
                }, f, indent=2)
                logger.info(f"Saved {len(self.proxies)} proxies to cache")
        except Exception as e:
            logger.error(f"Error saving proxy cache: {e}")
    
    def scrape_proxies(self) -> List[str]:
        """Scrape proxies from multiple sources"""
        proxies = []
        
        for source in self.PROXY_SOURCES:
            try:
                response = requests.get(
                    source,
                    timeout=10,
                    headers=self.user_agent_rotator.get_headers()
                )
                if response.status_code == 200:
                    proxy_list = response.text.strip().split('\r\n')
                    proxies.extend(proxy_list[:30])
                    logger.info(f"Scraped {len(proxy_list[:30])} proxies from {source}")
            except Exception as e:
                logger.warning(f"Error scraping from {source}: {e}")
        
        return proxies
    
    def validate_proxy(self, proxy: str) -> bool:
        """Validate if proxy is working"""
        test_urls = [
            "http://httpbin.org/ip",
            "http://api.ipify.org",
            "http://icanhazip.com",
        ]
        
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        
        for url in test_urls:
            try:
                response = requests.get(
                    url,
                    proxies=proxy_dict,
                    timeout=PROXY_TIMEOUT,
                    headers=self.user_agent_rotator.get_headers()
                )
                if response.status_code == 200:
                    return True
            except Exception:
                pass
        
        return False
    
    def refresh_proxies(self) -> int:
        """Refresh proxy pool with validation"""
        with self.lock:
            logger.info("Refreshing proxy pool...")
            
            new_proxies = self.scrape_proxies()
            
            valid_proxies = []
            for proxy in new_proxies:
                if proxy not in self.failed_proxies and self.validate_proxy(proxy):
                    valid_proxies.append({
                        'proxy': proxy,
                        'success_count': 0,
                        'fail_count': 0,
                        'last_used': None,
                        'added_at': time.time()
                    })
                    if len(valid_proxies) >= PROXY_POOL_SIZE:
                        break
            
            self.proxies = valid_proxies
            self.save_to_cache()
            logger.info(f"Proxy pool refreshed: {len(self.proxies)} valid proxies")
            
            return len(self.proxies)
    
    def get_random_proxy(self) -> Optional[Dict[str, Any]]:
        """Get random proxy from pool"""
        with self.lock:
            if time.time() - self.last_validation > self.validation_interval:
                self.refresh_proxies()
                self.last_validation = time.time()
            
            if not self.proxies:
                return None
            
            proxy = min(self.proxies, key=lambda p: p['fail_count'])
            proxy['last_used'] = time.time()
            return proxy.copy()
    
    def mark_success(self, proxy_str: str):
        """Mark proxy as successful"""
        with self.lock:
            for proxy in self.proxies:
                if proxy['proxy'] == proxy_str:
                    proxy['success_count'] += 1
                    proxy['fail_count'] = max(0, proxy['fail_count'] - 1)
    
    def mark_failure(self, proxy_str: str):
        """Mark proxy as failed"""
        with self.lock:
            for proxy in self.proxies:
                if proxy['proxy'] == proxy_str:
                    proxy['fail_count'] += 1
                    if proxy['fail_count'] >= MAX_PROXY_FAILURES:
                        self.failed_proxies.add(proxy_str)
                        logger.warning(f"Proxy {proxy_str} marked as permanently failed")

# ============================================================================
# DATABASE MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manages SQLite database for user data and statistics"""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        """Initialize database manager"""
        self.db_file = db_file
        self.lock = threading.Lock()
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_file)
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP,
                    total_requests INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0
                )
            ''')
            
            # Requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    video_url TEXT NOT NULL,
                    view_count INTEGER,
                    view_time INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Rate limiting table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    minute_count INTEGER DEFAULT 0,
                    hour_count INTEGER DEFAULT 0,
                    day_count INTEGER DEFAULT 0,
                    minute_reset TIMESTAMP,
                    hour_reset TIMESTAMP,
                    day_reset TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str) -> bool:
        """Add new user to database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO users 
                    (user_id, username, first_name, last_name, joined_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, datetime.now()))
                
                conn.commit()
                conn.close()
                logger.info(f"User {user_id} added to database")
                return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'is_admin': row[4],
                    'is_banned': row[5],
                    'joined_date': row[6],
                    'last_active': row[7],
                    'total_requests': row[8],
                    'total_views': row[9]
                }
        except Exception as e:
            logger.error(f"Error getting user: {e}")
        
        return None
    
    def update_user_activity(self, user_id: int):
        """Update user's last active time"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users SET last_active = ? WHERE user_id = ?
                ''', (datetime.now(), user_id))
                
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
    
    def add_request(self, user_id: int, video_url: str, view_count: int, view_time: int) -> bool:
        """Add new request to database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO requests 
                    (user_id, video_url, view_count, view_time, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, video_url, view_count, view_time, 'pending', datetime.now()))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error adding request: {e}")
            return False
    
    def get_user_requests(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recent requests"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM requests WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            requests_list = []
            for row in rows:
                requests_list.append({
                    'request_id': row[0],
                    'user_id': row[1],
                    'video_url': row[2],
                    'view_count': row[3],
                    'view_time': row[4],
                    'status': row[5],
                    'created_at': row[6],
                    'completed_at': row[7]
                })
            
            return requests_list
        except Exception as e:
            logger.error(f"Error getting user requests: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get bot statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM requests')
            total_requests = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(total_views) FROM users')
            total_views = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM requests WHERE status = "completed"')
            completed_requests = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'total_requests': total_requests,
                'total_views': total_views,
                'completed_requests': completed_requests
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Rate limiting system for users"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize rate limiter"""
        self.db = db_manager
        self.lock = threading.Lock()
    
    def check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """Check if user is within rate limits"""
        try:
            with self.lock:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                now = datetime.now()
                minute_ago = now - timedelta(minutes=1)
                hour_ago = now - timedelta(hours=1)
                day_ago = now - timedelta(days=1)
                
                cursor.execute('''
                    SELECT minute_count, hour_count, day_count FROM rate_limits
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    cursor.execute('''
                        INSERT INTO rate_limits (user_id, minute_count, hour_count, day_count)
                        VALUES (?, 0, 0, 0)
                    ''', (user_id,))
                    conn.commit()
                    conn.close()
                    return True, "OK"
                
                minute_count, hour_count, day_count = row
                
                if minute_count >= RATE_LIMIT_VISITS_PER_MINUTE:
                    conn.close()
                    return False, f"Minute limit exceeded ({minute_count}/{RATE_LIMIT_VISITS_PER_MINUTE})"
                
                if hour_count >= RATE_LIMIT_VISITS_PER_HOUR:
                    conn.close()
                    return False, f"Hour limit exceeded ({hour_count}/{RATE_LIMIT_VISITS_PER_HOUR})"
                
                if day_count >= RATE_LIMIT_VISITS_PER_DAY:
                    conn.close()
                    return False, f"Day limit exceeded ({day_count}/{RATE_LIMIT_VISITS_PER_DAY})"
                
                cursor.execute('''
                    UPDATE rate_limits 
                    SET minute_count = minute_count + 1,
                        hour_count = hour_count + 1,
                        day_count = day_count + 1
                    WHERE user_id = ?
                ''', (user_id,))
                
                conn.commit()
                conn.close()
                return True, "OK"
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False, "Error checking rate limit"

# ============================================================================
# YOUTUBE VIEW SIMULATOR
# ============================================================================

class YouTubeViewSimulator:
    """Simulates YouTube views with proxy rotation and anti-detection"""
    
    def __init__(self, proxy_manager: ProxyManager):
        """Initialize YouTube view simulator"""
        self.proxy_manager = proxy_manager
        self.user_agent_rotator = UserAgentRotator()
        self.session_cache = {}
        self.lock = threading.Lock()
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def validate_youtube_url(self, url: str) -> bool:
        """Validate if URL is a valid YouTube URL"""
        video_id = self.extract_video_id(url)
        return video_id is not None
    
    def simulate_view(self, video_url: str, view_time: int = DEFAULT_VIEW_TIME) -> Tuple[bool, str]:
        """Simulate a single YouTube view"""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return False, "Invalid YouTube URL"
            
            proxy_info = self.proxy_manager.get_random_proxy()
            if not proxy_info:
                return False, "No available proxies"
            
            proxy_dict = {
                "http": f"http://{proxy_info['proxy']}",
                "https": f"http://{proxy_info['proxy']}"
            }
            
            headers = self.user_agent_rotator.get_headers()
            
            try:
                response = requests.get(
                    f"https://www.youtube.com/watch?v={video_id}",
                    proxies=proxy_dict,
                    headers=headers,
                    timeout=PROXY_TIMEOUT,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    self.proxy_manager.mark_success(proxy_info['proxy'])
                    time.sleep(random.uniform(view_time * 0.8, view_time * 1.2))
                    return True, "View simulated successfully"
                else:
                    self.proxy_manager.mark_failure(proxy_info['proxy'])
                    return False, f"HTTP {response.status_code}"
            
            except Exception as e:
                self.proxy_manager.mark_failure(proxy_info['proxy'])
                return False, str(e)
        
        except Exception as e:
            logger.error(f"Error simulating view: {e}")
            return False, str(e)
    
    def simulate_views_batch(self, video_url: str, view_count: int, view_time: int = DEFAULT_VIEW_TIME) -> Dict:
        """Simulate multiple views in batch"""
        results = {
            'total': view_count,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for _ in range(view_count):
                future = executor.submit(self.simulate_view, video_url, view_time)
                futures.append(future)
            
            for future in as_completed(futures, timeout=THREAD_POOL_TIMEOUT):
                try:
                    success, message = future.result()
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(message)
                except FuturesTimeoutError:
                    results['failed'] += 1
                    results['errors'].append("Timeout")
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(str(e))
        
        return results

# ============================================================================
# TELEGRAM BOT HANDLERS
# ============================================================================

class TelegramBotHandlers:
    """Telegram bot command and message handlers"""
    
    def __init__(self, db_manager: DatabaseManager, proxy_manager: ProxyManager):
        """Initialize bot handlers"""
        self.db = db_manager
        self.proxy_manager = proxy_manager
        self.rate_limiter = RateLimiter(db_manager)
        self.youtube_simulator = YouTubeViewSimulator(proxy_manager)
        self.user_sessions = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            self.db.add_user(user.id, user.username, user.first_name, user.last_name)
            self.db.update_user_activity(user.id)
            
            # Use welcome message from config if available, otherwise use default
            welcome_text = ''
            if MODULES_LOADED and isinstance(MESSAGES, dict):
                welcome_text = MESSAGES.get('welcome', '')
            
            # Fallback message if config not available or empty
            if not welcome_text:
                welcome_text = (
                    "🎬 *Welcome to YouTube View Bot!*\n\n"
                    "This bot helps you simulate views on YouTube videos.\n\n"
                    "*Available Commands:*\n"
                    "🔗 /start - Start the bot\n"
                    "📊 /stats - View your statistics\n"
                    "🎥 /views - Simulate views on a video\n"
                    "📋 /history - View your request history\n"
                    "ℹ️ /help - Get help\n"
                    "⚙️ /settings - Adjust settings\n\n"
                    "*Admin Commands:*\n"
                    "👥 /users - View total users\n"
                    "📈 /botstats - View bot statistics\n"
                    "🔄 /proxies - Manage proxies\n"
                )
            
            keyboard = [
                [InlineKeyboardButton("📊 My Stats", callback_data="stats"),
                 InlineKeyboardButton("🎥 Add Views", callback_data="add_views")],
                [InlineKeyboardButton("📋 History", callback_data="history"),
                 InlineKeyboardButton("ℹ️ Help", callback_data="help")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            logger.info(f"User {user.id} started the bot")
        
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text("❌ Error starting bot. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            help_text = (
                "📚 *Help Guide*\n\n"
                "*How to use this bot:*\n\n"
                "1️⃣ Send a YouTube video link\n"
                "2️⃣ Specify the number of views you want\n"
                "3️⃣ Choose the view duration\n"
                "4️⃣ Confirm and start the process\n\n"
                "*Supported URL formats:*\n"
                "• https://www.youtube.com/watch?v=VIDEO_ID\n"
                "• https://youtu.be/VIDEO_ID\n"
                "• https://www.youtube.com/embed/VIDEO_ID\n\n"
                "*Rate Limits:*\n"
                f"• Per minute: {RATE_LIMIT_VISITS_PER_MINUTE}\n"
                f"• Per hour: {RATE_LIMIT_VISITS_PER_HOUR}\n"
                f"• Per day: {RATE_LIMIT_VISITS_PER_DAY}\n\n"
                "*View Duration:*\n"
                f"• Minimum: {MIN_VIEW_TIME} seconds\n"
                f"• Maximum: {MAX_VIEW_TIME} seconds\n"
                f"• Default: {DEFAULT_VIEW_TIME} seconds\n"
            )
            
            await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await update.message.reply_text("❌ Error retrieving help. Please try again.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            user_id = update.effective_user.id
            user_data = self.db.get_user(user_id)
            
            if not user_data:
                await update.message.reply_text("❌ User not found. Please use /start first.")
                return
            
            stats_text = (
                "📊 *Your Statistics*\n\n"
                f"👤 User ID: `{user_data['user_id']}`\n"
                f"📝 Username: @{user_data['username'] or 'N/A'}\n"
                f"📅 Joined: {user_data['joined_date']}\n"
                f"⏰ Last Active: {user_data['last_active'] or 'Never'}\n"
                f"📋 Total Requests: {user_data['total_requests']}\n"
                f"👁️ Total Views: {user_data['total_views']}\n"
            )
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text("❌ Error retrieving statistics. Please try again.")
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        try:
            user_id = update.effective_user.id
            requests_list = self.db.get_user_requests(user_id, limit=5)
            
            if not requests_list:
                await update.message.reply_text("📋 No request history found.")
                return
            
            history_text = "📋 *Your Recent Requests*\n\n"
            for req in requests_list:
                history_text += (
                    f"🔗 URL: {req['video_url'][:50]}...\n"
                    f"👁️ Views: {req['view_count']}\n"
                    f"⏱️ Duration: {req['view_time']}s\n"
                    f"✅ Status: {req['status']}\n"
                    f"📅 Date: {req['created_at']}\n\n"
                )
            
            await update.message.reply_text(history_text, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error in history_command: {e}")
            await update.message.reply_text("❌ Error retrieving history. Please try again.")
    
    async def views_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /views command - start conversation"""
        try:
            user_id = update.effective_user.id
            
            # Check rate limit
            allowed, message = self.rate_limiter.check_rate_limit(user_id)
            if not allowed:
                await update.message.reply_text(f"⚠️ Rate limit: {message}")
                return
            
            await update.message.reply_text(
                "🔗 Please send me a YouTube video link:\n\n"
                "Example: https://www.youtube.com/watch?v=VIDEO_ID"
            )
            
            return WAITING_FOR_URL
        
        except Exception as e:
            logger.error(f"Error in views_command: {e}")
            await update.message.reply_text("❌ Error starting view process. Please try again.")
    
    async def handle_url_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle YouTube URL input"""
        try:
            url = update.message.text.strip()
            user_id = update.effective_user.id
            
            if not self.youtube_simulator.validate_youtube_url(url):
                await update.message.reply_text(
                    "❌ Invalid YouTube URL. Please send a valid YouTube link."
                )
                return WAITING_FOR_URL
            
            self.user_sessions[user_id] = {'url': url}
            
            await update.message.reply_text(
                f"✅ URL accepted: {url}\n\n"
                f"👁️ How many views do you want? (1-1000)\n\n"
                f"Example: 100"
            )
            
            return WAITING_FOR_VIEWS
        
        except Exception as e:
            logger.error(f"Error in handle_url_input: {e}")
            await update.message.reply_text("❌ Error processing URL. Please try again.")
            return WAITING_FOR_URL
    
    async def handle_views_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle view count input"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.user_sessions:
                await update.message.reply_text("❌ Session expired. Please use /views again.")
                return
            
            try:
                view_count = int(update.message.text.strip())
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid number. Please enter a valid number (1-1000)."
                )
                return WAITING_FOR_VIEWS
            
            if view_count < 1 or view_count > 1000:
                await update.message.reply_text(
                    "❌ Invalid range. Please enter a number between 1 and 1000."
                )
                return WAITING_FOR_VIEWS
            
            self.user_sessions[user_id]['views'] = view_count
            
            await update.message.reply_text(
                f"⏱️ How long should each view last? (5-3600 seconds)\n\n"
                f"Example: 30 (for 30 seconds)"
            )
            
            return WAITING_FOR_TIME
        
        except Exception as e:
            logger.error(f"Error in handle_views_input: {e}")
            await update.message.reply_text("❌ Error processing view count. Please try again.")
            return WAITING_FOR_VIEWS
    
    async def handle_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle view time input"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.user_sessions:
                await update.message.reply_text("❌ Session expired. Please use /views again.")
                return
            
            try:
                view_time = int(update.message.text.strip())
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid number. Please enter a valid number."
                )
                return WAITING_FOR_TIME
            
            if view_time < MIN_VIEW_TIME or view_time > MAX_VIEW_TIME:
                await update.message.reply_text(
                    f"❌ Invalid range. Please enter a number between {MIN_VIEW_TIME} and {MAX_VIEW_TIME}."
                )
                return WAITING_FOR_TIME
            
            self.user_sessions[user_id]['time'] = view_time
            
            session = self.user_sessions[user_id]
            confirmation_text = (
                "📋 *Confirm Your Request*\n\n"
                f"🔗 Video URL: {session['url']}\n"
                f"👁️ Views: {session['views']}\n"
                f"⏱️ Duration per view: {session['time']}s\n\n"
                "✅ Confirm to start the process?"
            )
            
            keyboard = [
                [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_views_{user_id}"),
                 InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(confirmation_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            
            return WAITING_FOR_CONFIRMATION
        
        except Exception as e:
            logger.error(f"Error in handle_time_input: {e}")
            await update.message.reply_text("❌ Error processing view time. Please try again.")
            return WAITING_FOR_TIME
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            
            if query.data == "stats":
                await self.stats_command(update, context)
            
            elif query.data == "add_views":
                await query.edit_message_text("🔗 Please send me a YouTube video link:")
                return WAITING_FOR_URL
            
            elif query.data == "history":
                await self.history_command(update, context)
            
            elif query.data == "help":
                await self.help_command(update, context)
            
            elif query.data == "cancel":
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                await query.edit_message_text("❌ Request cancelled.")
            
            elif query.data.startswith("confirm_views_"):
                if user_id in self.user_sessions:
                    session = self.user_sessions[user_id]
                    
                    await query.edit_message_text(
                        "⏳ Processing your request...\n"
                        "This may take a few moments."
                    )
                    
                    # Add request to database
                    self.db.add_request(
                        user_id,
                        session['url'],
                        session['views'],
                        session['time']
                    )
                    
                    # Simulate views
                    results = self.youtube_simulator.simulate_views_batch(
                        session['url'],
                        session['views'],
                        session['time']
                    )
                    
                    result_text = (
                        "✅ *Process Completed*\n\n"
                        f"👁️ Total Views: {results['total']}\n"
                        f"✅ Successful: {results['successful']}\n"
                        f"❌ Failed: {results['failed']}\n"
                        f"Success Rate: {(results['successful']/results['total']*100):.1f}%\n"
                    )
                    
                    await query.edit_message_text(result_text, parse_mode=ParseMode.MARKDOWN)
                    
                    del self.user_sessions[user_id]
        
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            await query.answer("❌ Error processing request", show_alert=True)

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

class AdminCommands:
    """Admin-only commands"""
    
    def __init__(self, db_manager: DatabaseManager, proxy_manager: ProxyManager):
        """Initialize admin commands"""
        self.db = db_manager
        self.proxy_manager = proxy_manager
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMIN_IDS
    
    async def botstats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /botstats command"""
        try:
            if not await self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You don't have permission to use this command.")
                return
            
            stats = self.db.get_statistics()
            
            stats_text = (
                "📊 *Bot Statistics*\n\n"
                f"👥 Total Users: {stats.get('total_users', 0)}\n"
                f"📋 Total Requests: {stats.get('total_requests', 0)}\n"
                f"👁️ Total Views: {stats.get('total_views', 0)}\n"
                f"✅ Completed Requests: {stats.get('completed_requests', 0)}\n"
            )
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error in botstats_command: {e}")
            await update.message.reply_text("❌ Error retrieving bot statistics.")
    
    async def proxies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /proxies command"""
        try:
            if not await self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You don't have permission to use this command.")
                return
            
            proxy_count = len(self.proxy_manager.proxies)
            
            proxies_text = (
                "🔄 *Proxy Management*\n\n"
                f"📊 Active Proxies: {proxy_count}\n"
                f"🎯 Pool Size: {PROXY_POOL_SIZE}\n"
                f"⏱️ Validation Interval: {PROXY_VALIDATION_INTERVAL}s\n\n"
                "Use /refresh_proxies to refresh the proxy pool."
            )
            
            await update.message.reply_text(proxies_text, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error in proxies_command: {e}")
            await update.message.reply_text("❌ Error retrieving proxy information.")
    
    async def refresh_proxies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh_proxies command"""
        try:
            if not await self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You don't have permission to use this command.")
                return
            
            await update.message.reply_text("⏳ Refreshing proxy pool...")
            
            count = self.proxy_manager.refresh_proxies()
            
            await update.message.reply_text(
                f"✅ Proxy pool refreshed!\n"
                f"📊 Active proxies: {count}"
            )
        
        except Exception as e:
            logger.error(f"Error in refresh_proxies_command: {e}")
            await update.message.reply_text("❌ Error refreshing proxies.")

# ============================================================================
# MAIN BOT APPLICATION
# ============================================================================

class TelegramYouTubeBot:
    """Main Telegram YouTube bot application"""
    
    def __init__(self, token: str):
        """Initialize bot and all components"""
        self.token = token
        self.db_manager = DatabaseManager()
        self.proxy_manager = ProxyManager()
        self.handlers = TelegramBotHandlers(self.db_manager, self.proxy_manager)
        self.admin_commands = AdminCommands(self.db_manager, self.proxy_manager)
        self.application = None
        
        # Initialize advanced features if modules are loaded
        if MODULES_LOADED:
            logger.info("🔧 Initializing advanced features...")
            try:
                self.analytics = AnalyticsEngine()
                logger.info("  ✅ Analytics Engine initialized")
            except Exception as e:
                logger.warning(f"  ⚠️  Analytics Engine failed: {e}")
                self.analytics = None
            
            try:
                self.notifications = NotificationManager()
                logger.info("  ✅ Notification Manager initialized")
            except Exception as e:
                logger.warning(f"  ⚠️  Notification Manager failed: {e}")
                self.notifications = None
            
            try:
                self.scheduler = TaskScheduler()
                logger.info("  ✅ Task Scheduler initialized")
            except Exception as e:
                logger.warning(f"  ⚠️  Task Scheduler failed: {e}")
                self.scheduler = None
            
            try:
                self.preferences = UserPreferences()
                logger.info("  ✅ User Preferences initialized")
            except Exception as e:
                logger.warning(f"  ⚠️  User Preferences failed: {e}")
                self.preferences = None
        else:
            self.analytics = None
            self.notifications = None
            self.scheduler = None
            self.preferences = None
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        if not self.application:
            logger.error("Application not initialized")
            return
        
        # Conversation handler for views
        views_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("views", self.handlers.views_command)],
            states={
                WAITING_FOR_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_url_input)],
                WAITING_FOR_VIEWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_views_input)],
                WAITING_FOR_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_time_input)],
                WAITING_FOR_CONFIRMATION: [CallbackQueryHandler(self.handlers.button_callback)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_handler)],
            per_message=False,
        )
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("history", self.handlers.history_command))
        self.application.add_handler(views_conv_handler)
        
        # Admin commands
        self.application.add_handler(CommandHandler("botstats", self.admin_commands.botstats_command))
        self.application.add_handler(CommandHandler("proxies", self.admin_commands.proxies_command))
        self.application.add_handler(CommandHandler("refresh_proxies", self.admin_commands.refresh_proxies_command))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handlers.button_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Bot handlers setup completed")
    
    async def cancel_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancel command"""
        user_id = update.effective_user.id
        if user_id in self.handlers.user_sessions:
            del self.handlers.user_sessions[user_id]
        
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
            except Exception as e:
                logger.error(f"Error sending error message: {e}")
    
    async def startup(self, application):
        """Startup tasks"""
        logger.info("Bot starting up...")
        
        # Load proxies from cache
        if not self.proxy_manager.load_from_cache():
            logger.info("No cached proxies found, refreshing proxy pool...")
            self.proxy_manager.refresh_proxies()
        
        logger.info("Bot startup completed")
    
    async def shutdown(self, application):
        """Shutdown tasks"""
        logger.info("Bot shutting down...")
        self.proxy_manager.save_to_cache()
        logger.info("Bot shutdown completed")
    
    def run(self):
        """Run the bot"""
        try:
            self.application = Application.builder().token(self.token).build()
            
            self.setup_handlers()
            
            self.application.post_init = self.startup
            self.application.post_shutdown = self.shutdown
            
            logger.info("Starting bot polling...")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        
        except Exception as e:
            logger.error(f"Fatal error running bot: {e}")
            traceback.print_exc()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point - Starts all bot components"""
    logger.info("=" * 80)
    logger.info("TELEGRAM YOUTUBE VIEW BOT - STARTING")
    logger.info("=" * 80)
    logger.info(f"Version: {BOT_VERSION if MODULES_LOADED else '2.0'}")
    logger.info(f"Author: @LEGEND_BL")
    logger.info(f"Modules Loaded: {'✅ YES' if MODULES_LOADED else '⚠️  STANDALONE MODE'}")
    logger.info("=" * 80)
    
    # Validate configuration
    if MODULES_LOADED:
        valid, message = validate_config()
        if not valid:
            logger.error(f"❌ Configuration validation failed: {message}")
            sys.exit(1)
        logger.info(f"✅ Configuration validated: {message}")
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or BOT_TOKEN == "":
        logger.error("❌ BOT_TOKEN not configured. Please set TELEGRAM_BOT_TOKEN environment variable.")
        logger.error("   Export it: export TELEGRAM_BOT_TOKEN='your_token_here'")
        logger.error("   Or add it to a .env file (see .env.example)")
        sys.exit(1)
    
    logger.info("✅ Bot token configured")
    logger.info(f"📊 Max Workers: {MAX_WORKERS}")
    logger.info(f"🔄 Proxy Pool Size: {PROXY_POOL_SIZE}")
    logger.info(f"⏱️  View Time: {MIN_VIEW_TIME}s - {MAX_VIEW_TIME}s")
    logger.info("=" * 80)
    
    try:
        bot = TelegramYouTubeBot(BOT_TOKEN)
        logger.info("🚀 Starting bot polling...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Bot interrupted by user - Shutting down gracefully")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
