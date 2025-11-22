#!/usr/bin/env python3
"""
BOT FEATURES AND EXTENSIONS
Advanced features including analytics, scheduling, notifications, and plugins.

Author: Manus Bot Development
Version: 2.0
"""

import os
import json
import time
import logging
import threading
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import pickle
import queue

logger = logging.getLogger(__name__)

# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class AnalyticsEngine:
    """Advanced analytics and reporting engine"""
    
    def __init__(self, db_file: str = "analytics.db"):
        """Initialize analytics engine"""
        self.db_file = db_file
        self.lock = threading.Lock()
        self.events = queue.Queue()
        self.init_database()
        self.start_event_processor()
    
    def init_database(self):
        """Initialize analytics database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_analytics (
                    user_id INTEGER PRIMARY KEY,
                    total_events INTEGER DEFAULT 0,
                    last_event TIMESTAMP,
                    engagement_score REAL DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Analytics database initialized")
        except Exception as e:
            logger.error(f"Error initializing analytics database: {e}")
    
    def track_event(self, event_type: str, user_id: Optional[int] = None, data: Optional[Dict] = None):
        """Track an event"""
        try:
            event = {
                'event_type': event_type,
                'user_id': user_id,
                'data': json.dumps(data) if data else None,
                'timestamp': datetime.now()
            }
            self.events.put(event)
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
    
    def start_event_processor(self):
        """Start background event processor"""
        thread = threading.Thread(target=self._process_events, daemon=True)
        thread.start()
    
    def _process_events(self):
        """Process events from queue"""
        while True:
            try:
                event = self.events.get(timeout=5)
                self._save_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    def _save_event(self, event: Dict):
        """Save event to database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO events (event_type, user_id, data, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (event['event_type'], event['user_id'], event['data'], event['timestamp']))
                
                # Update user analytics
                if event['user_id']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO user_analytics (user_id, total_events, last_event)
                        VALUES (?, 1, ?)
                    ''', (event['user_id'], event['timestamp']))
                    
                    cursor.execute('''
                        UPDATE user_analytics 
                        SET total_events = total_events + 1, last_event = ?
                        WHERE user_id = ?
                    ''', (event['timestamp'], event['user_id']))
                
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error saving event: {e}")
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """Get user analytics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_events, last_event, engagement_score
                FROM user_analytics WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'total_events': row[0],
                    'last_event': row[1],
                    'engagement_score': row[2]
                }
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
        
        return {}
    
    def get_event_statistics(self, days: int = 7) -> Dict:
        """Get event statistics for last N days"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT event_type, COUNT(*) as count
                FROM events WHERE timestamp > ?
                GROUP BY event_type
            ''', (since,))
            
            rows = cursor.fetchall()
            conn.close()
            
            stats = {}
            for event_type, count in rows:
                stats[event_type] = count
            
            return stats
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}

# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

class NotificationManager:
    """Manages notifications and alerts"""
    
    def __init__(self):
        """Initialize notification manager"""
        self.notifications: Dict[int, List[Dict]] = defaultdict(list)
        self.lock = threading.Lock()
        self.max_notifications = 100
    
    def send_notification(self, user_id: int, title: str, message: str, 
                         notification_type: str = "info", data: Optional[Dict] = None):
        """Send notification to user"""
        try:
            with self.lock:
                notification = {
                    'id': len(self.notifications[user_id]),
                    'title': title,
                    'message': message,
                    'type': notification_type,
                    'data': data or {},
                    'timestamp': datetime.now(),
                    'read': False
                }
                
                self.notifications[user_id].append(notification)
                
                # Keep only last N notifications
                if len(self.notifications[user_id]) > self.max_notifications:
                    self.notifications[user_id] = self.notifications[user_id][-self.max_notifications:]
                
                logger.info(f"Notification sent to user {user_id}: {title}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict]:
        """Get user notifications"""
        with self.lock:
            notifications = self.notifications.get(user_id, [])
            
            if unread_only:
                notifications = [n for n in notifications if not n['read']]
            
            return notifications.copy()
    
    def mark_as_read(self, user_id: int, notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            with self.lock:
                if user_id in self.notifications:
                    for notif in self.notifications[user_id]:
                        if notif['id'] == notification_id:
                            notif['read'] = True
                            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
        
        return False
    
    def clear_notifications(self, user_id: int) -> bool:
        """Clear all notifications for user"""
        try:
            with self.lock:
                if user_id in self.notifications:
                    self.notifications[user_id] = []
                    return True
        except Exception as e:
            logger.error(f"Error clearing notifications: {e}")
        
        return False

# ============================================================================
# SCHEDULING SYSTEM
# ============================================================================

class TaskScheduler:
    """Schedule and manage recurring tasks"""
    
    def __init__(self):
        """Initialize task scheduler"""
        self.tasks: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.running = False
        self.start()
    
    def add_task(self, task_id: str, interval: int, callback: Callable, 
                 args: tuple = (), kwargs: dict = None):
        """Add a scheduled task"""
        try:
            with self.lock:
                self.tasks[task_id] = {
                    'interval': interval,
                    'callback': callback,
                    'args': args,
                    'kwargs': kwargs or {},
                    'last_run': None,
                    'next_run': time.time() + interval,
                    'enabled': True
                }
                logger.info(f"Task {task_id} scheduled with interval {interval}s")
        except Exception as e:
            logger.error(f"Error adding task: {e}")
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        try:
            with self.lock:
                if task_id in self.tasks:
                    del self.tasks[task_id]
                    logger.info(f"Task {task_id} removed")
                    return True
        except Exception as e:
            logger.error(f"Error removing task: {e}")
        
        return False
    
    def start(self):
        """Start the scheduler"""
        self.running = True
        thread = threading.Thread(target=self._run_scheduler, daemon=True)
        thread.start()
        logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                current_time = time.time()
                
                with self.lock:
                    for task_id, task in self.tasks.items():
                        if task['enabled'] and current_time >= task['next_run']:
                            try:
                                task['callback'](*task['args'], **task['kwargs'])
                                task['last_run'] = current_time
                                task['next_run'] = current_time + task['interval']
                            except Exception as e:
                                logger.error(f"Error executing task {task_id}: {e}")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Get task information"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id].copy()
                # Remove callback for serialization
                task.pop('callback', None)
                return task
        
        return None

# ============================================================================
# PLUGIN SYSTEM
# ============================================================================

class PluginManager:
    """Manage bot plugins and extensions"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        """Initialize plugin manager"""
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Any] = {}
        self.hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = threading.Lock()
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin with validation"""
        try:
            # Validate plugin name (alphanumeric and underscore only)
            if not re.match(r'^[a-zA-Z0-9_]+$', plugin_name):
                logger.error(f"Invalid plugin name: {plugin_name}")
                return False
            
            plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
            
            if not os.path.exists(plugin_path):
                logger.error(f"Plugin file not found: {plugin_path}")
                return False
            
            # Security: Check that plugin_path is within plugins_dir
            real_plugin_path = os.path.realpath(plugin_path)
            real_plugins_dir = os.path.realpath(self.plugins_dir)
            if not real_plugin_path.startswith(real_plugins_dir):
                logger.error(f"Security: Plugin path outside plugins directory: {plugin_path}")
                return False
            
            # Import plugin in restricted manner
            import importlib.util
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Cannot load plugin spec: {plugin_name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            with self.lock:
                self.plugins[plugin_name] = module
            
            logger.info(f"Plugin {plugin_name} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        with self.lock:
            self.hooks[hook_name].append(callback)
            logger.info(f"Hook {hook_name} registered")
    
    def execute_hook(self, hook_name: str, *args, **kwargs):
        """Execute all callbacks for a hook"""
        with self.lock:
            callbacks = self.hooks.get(hook_name, []).copy()
        
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error executing hook {hook_name}: {e}")
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get loaded plugin"""
        with self.lock:
            return self.plugins.get(plugin_name)

# ============================================================================
# USER PREFERENCES
# ============================================================================

class UserPreferences:
    """Manage user preferences and settings"""
    
    def __init__(self, db_file: str = "user_preferences.db"):
        """Initialize user preferences"""
        self.db_file = db_file
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize preferences database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id INTEGER PRIMARY KEY,
                    preferences TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing preferences database: {e}")
    
    def set_preference(self, user_id: int, key: str, value: Any) -> bool:
        """Set user preference"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                # Get existing preferences
                cursor.execute('SELECT preferences FROM preferences WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    prefs = json.loads(row[0])
                else:
                    prefs = {}
                
                prefs[key] = value
                
                cursor.execute('''
                    INSERT OR REPLACE INTO preferences (user_id, preferences, updated_at)
                    VALUES (?, ?, ?)
                ''', (user_id, json.dumps(prefs), datetime.now()))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error setting preference: {e}")
            return False
    
    def get_preference(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get user preference"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT preferences FROM preferences WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                prefs = json.loads(row[0])
                return prefs.get(key, default)
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
        
        return default
    
    def get_all_preferences(self, user_id: int) -> Dict:
        """Get all user preferences"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT preferences FROM preferences WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
        
        return {}

# ============================================================================
# COMMAND SYSTEM
# ============================================================================

class CommandRegistry:
    """Registry for custom commands"""
    
    def __init__(self):
        """Initialize command registry"""
        self.commands: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def register_command(self, name: str, handler: Callable, 
                        description: str = "", aliases: List[str] = None):
        """Register a command"""
        try:
            with self.lock:
                self.commands[name] = {
                    'handler': handler,
                    'description': description,
                    'aliases': aliases or [],
                    'registered_at': datetime.now()
                }
                logger.info(f"Command {name} registered")
        except Exception as e:
            logger.error(f"Error registering command: {e}")
    
    def unregister_command(self, name: str) -> bool:
        """Unregister a command"""
        try:
            with self.lock:
                if name in self.commands:
                    del self.commands[name]
                    logger.info(f"Command {name} unregistered")
                    return True
        except Exception as e:
            logger.error(f"Error unregistering command: {e}")
        
        return False
    
    def execute_command(self, name: str, *args, **kwargs) -> Any:
        """Execute a command"""
        try:
            with self.lock:
                if name in self.commands:
                    handler = self.commands[name]['handler']
                    return handler(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing command {name}: {e}")
        
        return None
    
    def get_commands(self) -> List[Dict]:
        """Get all registered commands"""
        with self.lock:
            commands_list = []
            for name, cmd_info in self.commands.items():
                commands_list.append({
                    'name': name,
                    'description': cmd_info['description'],
                    'aliases': cmd_info['aliases']
                })
            return commands_list

# ============================================================================
# EXPORT ALL FEATURES
# ============================================================================

__all__ = [
    'AnalyticsEngine',
    'NotificationManager',
    'TaskScheduler',
    'PluginManager',
    'UserPreferences',
    'CommandRegistry',
]
