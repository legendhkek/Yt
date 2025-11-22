#!/usr/bin/env python3
"""
BOT UTILITIES AND HELPER MODULES
Comprehensive utility functions, decorators, and helper classes for the Telegram bot.
Includes caching, validation, formatting, and advanced features.

Author: Manus Bot Development
Version: 2.0
"""

import os
import json
import time
import hashlib
import logging
import threading
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from functools import wraps, lru_cache
from collections import OrderedDict
import pickle
import base64
import re
from urllib.parse import urlparse, parse_qs, quote, unquote

logger = logging.getLogger(__name__)

# ============================================================================
# CACHING SYSTEM
# ============================================================================

class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, max_size: int = 1000, expiry_time: int = 3600):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items to store
            expiry_time: Time in seconds before cache entries expire
        """
        self.max_size = max_size
        self.expiry_time = expiry_time
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check if expired
            if time.time() - self.timestamps[key] > self.expiry_time:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            # Remove oldest if cache is full
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

# ============================================================================
# DECORATORS
# ============================================================================

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

def rate_limit(calls: int = 10, period: float = 60.0):
    """
    Decorator to rate limit function calls
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
    """
    def decorator(func: Callable) -> Callable:
        call_times = []
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                
                # Remove old calls outside the period
                call_times[:] = [t for t in call_times if now - t < period]
                
                if len(call_times) >= calls:
                    sleep_time = period - (now - call_times[0])
                    if sleep_time > 0:
                        logger.warning(f"Rate limit reached for {func.__name__}. Sleeping {sleep_time}s")
                        time.sleep(sleep_time)
                
                call_times.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def async_task(func: Callable) -> Callable:
    """Decorator to run function asynchronously"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    
    return wrapper

def timed_cache(seconds: int = 300):
    """Decorator for time-based caching"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            
            with lock:
                now = time.time()
                
                if key in cache and now - cache_times[key] < seconds:
                    return cache[key]
                
                result = func(*args, **kwargs)
                cache[key] = result
                cache_times[key] = now
                
                return result
        
        return wrapper
    return decorator

# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """Validate YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
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
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number"""
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text

# ============================================================================
# FORMATTING UTILITIES
# ============================================================================

class Formatter:
    """Text formatting utilities"""
    
    @staticmethod
    def format_number(num: int) -> str:
        """Format number with thousands separator"""
        return f"{num:,}"
    
    @staticmethod
    def format_bytes(bytes_size: int) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        
        return f"{bytes_size:.2f} PB"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration to human-readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime to readable string"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def format_percentage(value: float, total: float) -> str:
        """Format percentage"""
        if total == 0:
            return "0%"
        percentage = (value / total) * 100
        return f"{percentage:.1f}%"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def create_progress_bar(current: int, total: int, width: int = 20) -> str:
        """Create ASCII progress bar"""
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        filled = int(width * current // total)
        bar = '█' * filled + '░' * (width - filled)
        
        return f"[{bar}] {percentage:.0f}%"

# ============================================================================
# SECURITY UTILITIES
# ============================================================================

class SecurityUtils:
    """Security and encryption utilities"""
    
    @staticmethod
    def hash_string(text: str, algorithm: str = 'sha256') -> str:
        """Hash string using specified algorithm"""
        if algorithm == 'sha256':
            return hashlib.sha256(text.encode()).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(text.encode()).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(text.encode()).hexdigest()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    @staticmethod
    def encode_base64(text: str) -> str:
        """Encode string to base64"""
        return base64.b64encode(text.encode()).decode()
    
    @staticmethod
    def decode_base64(encoded: str) -> str:
        """Decode base64 string"""
        try:
            return base64.b64decode(encoded).decode()
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return ""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate random token"""
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """Mask sensitive data"""
        if len(data) <= visible_chars:
            return "*" * len(data)
        
        visible = data[:visible_chars]
        masked = "*" * (len(data) - visible_chars)
        return visible + masked

# ============================================================================
# JSON UTILITIES
# ============================================================================

class JSONUtils:
    """JSON handling utilities"""
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Dict]:
        """Load JSON from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            return None
    
    @staticmethod
    def save_json(data: Dict, file_path: str) -> bool:
        """Save JSON to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False
    
    @staticmethod
    def merge_json(dict1: Dict, dict2: Dict) -> Dict:
        """Merge two JSON dictionaries"""
        result = dict1.copy()
        result.update(dict2)
        return result
    
    @staticmethod
    def get_nested_value(data: Dict, key_path: str, default: Any = None) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

# ============================================================================
# STATISTICS UTILITIES
# ============================================================================

class Statistics:
    """Statistical analysis utilities"""
    
    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """Calculate average of values"""
        if not values:
            return 0
        return sum(values) / len(values)
    
    @staticmethod
    def calculate_median(values: List[float]) -> float:
        """Calculate median of values"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    @staticmethod
    def calculate_std_dev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0
        
        mean = Statistics.calculate_average(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * len(sorted_values)
        
        if index == int(index):
            return sorted_values[int(index) - 1]
        else:
            return sorted_values[int(index)]

# ============================================================================
# FILE UTILITIES
# ============================================================================

class FileUtils:
    """File handling utilities"""
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists"""
        return os.path.isfile(file_path)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0
    
    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        """Read file contents"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None
    
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """Write content to file"""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            return False
    
    @staticmethod
    def append_file(file_path: str, content: str) -> bool:
        """Append content to file"""
        try:
            with open(file_path, 'a') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error appending to file: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    @staticmethod
    def create_directory(dir_path: str) -> bool:
        """Create directory"""
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            return False

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

class LoggingUtils:
    """Logging utilities"""
    
    @staticmethod
    def setup_file_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
        """Setup file logger"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    @staticmethod
    def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
        """Log exception with context"""
        logger.error(f"Exception in {context}: {exception}", exc_info=True)

# ============================================================================
# PERFORMANCE UTILITIES
# ============================================================================

class PerformanceUtils:
    """Performance monitoring utilities"""
    
    @staticmethod
    def measure_execution_time(func: Callable) -> Callable:
        """Decorator to measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            return result
        
        return wrapper
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            return {
                'rss': mem_info.rss,  # Resident Set Size
                'vms': mem_info.vms,  # Virtual Memory Size
                'percent': process.memory_percent()
            }
        except ImportError:
            logger.warning("psutil not installed, cannot get memory usage")
            return {}

# ============================================================================
# EXPORT ALL UTILITIES
# ============================================================================

__all__ = [
    'LRUCache',
    'retry_on_failure',
    'rate_limit',
    'async_task',
    'timed_cache',
    'Validator',
    'Formatter',
    'SecurityUtils',
    'JSONUtils',
    'Statistics',
    'FileUtils',
    'LoggingUtils',
    'PerformanceUtils',
]
