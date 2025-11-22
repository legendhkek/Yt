#!/usr/bin/env python3
"""
SETUP AND INSTALLATION SCRIPT
Automated setup and installation for the Telegram YouTube View Bot.

Author: Manus Bot Development
Version: 2.0
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from typing import Optional

class BotSetup:
    """Bot setup and installation manager"""
    
    def __init__(self):
        """Initialize setup manager"""
        self.bot_dir = Path(__file__).parent
        self.config_file = self.bot_dir / "bot_config.json"
        self.requirements_file = self.bot_dir / "requirements.txt"
    
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70 + "\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"✅ {text}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"❌ {text}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"ℹ️  {text}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"⚠️  {text}")
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        self.print_info(f"Python version: {sys.version}")
        
        if sys.version_info < (3, 8):
            self.print_error("Python 3.8 or higher is required")
            return False
        
        self.print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
        return True
    
    def check_system(self) -> bool:
        """Check system compatibility"""
        self.print_info(f"Operating System: {platform.system()} {platform.release()}")
        self.print_info(f"Architecture: {platform.machine()}")
        
        if platform.system() not in ["Linux", "Darwin", "Windows"]:
            self.print_warning("This OS may not be fully supported")
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install required dependencies"""
        self.print_header("Installing Dependencies")
        
        if not self.requirements_file.exists():
            self.print_error(f"Requirements file not found: {self.requirements_file}")
            return False
        
        try:
            self.print_info("Installing packages from requirements.txt...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "-r", str(self.requirements_file)
            ])
            self.print_success("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        self.print_header("Creating Directories")
        
        directories = [
            self.bot_dir / "logs",
            self.bot_dir / "data",
            self.bot_dir / "plugins",
            self.bot_dir / "cache",
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Created directory: {directory}")
            except Exception as e:
                self.print_error(f"Failed to create directory {directory}: {e}")
                return False
        
        return True
    
    def setup_configuration(self) -> bool:
        """Setup bot configuration"""
        self.print_header("Bot Configuration")
        
        if self.config_file.exists():
            response = input("Configuration file already exists. Overwrite? (y/n): ").lower()
            if response != 'y':
                self.print_info("Using existing configuration")
                return True
        
        print("\nEnter bot configuration (press Enter for defaults):\n")
        
        bot_token = input("Telegram Bot Token: ").strip()
        if not bot_token:
            self.print_error("Bot token is required")
            return False
        
        admin_ids = input("Admin IDs (comma-separated) [123456789]: ").strip()
        if not admin_ids:
            admin_ids = "123456789"
        
        admin_ids = [int(x.strip()) for x in admin_ids.split(",")]
        
        rate_limit_minute = input("Rate limit per minute [15]: ").strip()
        rate_limit_minute = int(rate_limit_minute) if rate_limit_minute else 15
        
        rate_limit_hour = input("Rate limit per hour [150]: ").strip()
        rate_limit_hour = int(rate_limit_hour) if rate_limit_hour else 150
        
        rate_limit_day = input("Rate limit per day [1000]: ").strip()
        rate_limit_day = int(rate_limit_day) if rate_limit_day else 1000
        
        proxy_pool_size = input("Proxy pool size [150]: ").strip()
        proxy_pool_size = int(proxy_pool_size) if proxy_pool_size else 150
        
        max_workers = input("Max workers [75]: ").strip()
        max_workers = int(max_workers) if max_workers else 75
        
        config = {
            "BOT_TOKEN": bot_token,
            "BOT_NAME": "YouTube View Bot",
            "BOT_VERSION": "2.0",
            "ADMIN_IDS": admin_ids,
            "OWNER_ID": admin_ids[0] if admin_ids else 123456789,
            "RATE_LIMIT_VISITS_PER_MINUTE": rate_limit_minute,
            "RATE_LIMIT_VISITS_PER_HOUR": rate_limit_hour,
            "RATE_LIMIT_VISITS_PER_DAY": rate_limit_day,
            "PROXY_POOL_SIZE": proxy_pool_size,
            "MAX_WORKERS": max_workers,
            "ENABLE_ANALYTICS": True,
            "ENABLE_NOTIFICATIONS": True,
            "ENABLE_SCHEDULING": True,
            "ENABLE_PLUGINS": False,
            "ENABLE_PREMIUM": False,
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.print_success(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.print_error(f"Failed to save configuration: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Setup environment variables"""
        self.print_header("Environment Setup")
        
        env_file = self.bot_dir / ".env"
        
        if env_file.exists():
            response = input(".env file already exists. Overwrite? (y/n): ").lower()
            if response != 'y':
                self.print_info("Using existing .env file")
                return True
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            env_content = f"""# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN={config.get('BOT_TOKEN', '')}
BOT_NAME={config.get('BOT_NAME', 'YouTube View Bot')}
LOG_LEVEL=INFO

# Admin Configuration
ADMIN_IDS={','.join(map(str, config.get('ADMIN_IDS', [123456789])))}
OWNER_ID={config.get('OWNER_ID', 123456789)}

# Rate Limiting
RATE_LIMIT_VISITS_PER_MINUTE={config.get('RATE_LIMIT_VISITS_PER_MINUTE', 15)}
RATE_LIMIT_VISITS_PER_HOUR={config.get('RATE_LIMIT_VISITS_PER_HOUR', 150)}
RATE_LIMIT_VISITS_PER_DAY={config.get('RATE_LIMIT_VISITS_PER_DAY', 1000)}

# Proxy Configuration
PROXY_POOL_SIZE={config.get('PROXY_POOL_SIZE', 150)}
MAX_WORKERS={config.get('MAX_WORKERS', 75)}

# Feature Flags
ENABLE_ANALYTICS={str(config.get('ENABLE_ANALYTICS', True))}
ENABLE_NOTIFICATIONS={str(config.get('ENABLE_NOTIFICATIONS', True))}
ENABLE_SCHEDULING={str(config.get('ENABLE_SCHEDULING', True))}
ENABLE_PLUGINS={str(config.get('ENABLE_PLUGINS', False))}
ENABLE_PREMIUM={str(config.get('ENABLE_PREMIUM', False))}
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            self.print_success(f"Environment file created: {env_file}")
            return True
        except Exception as e:
            self.print_error(f"Failed to create environment file: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify installation"""
        self.print_header("Verifying Installation")
        
        files_to_check = [
            "telegram_bot_main.py",
            "bot_utilities.py",
            "bot_features.py",
            "config.py",
            "requirements.txt",
            "README.md",
        ]
        
        all_exist = True
        for file in files_to_check:
            file_path = self.bot_dir / file
            if file_path.exists():
                self.print_success(f"Found: {file}")
            else:
                self.print_error(f"Missing: {file}")
                all_exist = False
        
        if not all_exist:
            return False
        
        # Check Python packages
        self.print_info("Checking Python packages...")
        try:
            import telegram
            self.print_success("python-telegram-bot is installed")
        except ImportError:
            self.print_error("python-telegram-bot is not installed")
            return False
        
        try:
            import requests
            self.print_success("requests is installed")
        except ImportError:
            self.print_error("requests is not installed")
            return False
        
        return True
    
    def run_setup(self) -> bool:
        """Run complete setup"""
        self.print_header("YouTube View Bot - Setup Wizard")
        self.print_info("Version 2.0 - Manus Bot Development")
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Check system
        if not self.check_system():
            return False
        
        # Create directories
        if not self.create_directories():
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Setup configuration
        if not self.setup_configuration():
            return False
        
        # Setup environment
        if not self.setup_environment():
            return False
        
        # Verify installation
        if not self.verify_installation():
            return False
        
        self.print_header("Setup Complete!")
        self.print_success("Bot is ready to run")
        self.print_info("\nTo start the bot, run:")
        self.print_info("  python3 telegram_bot_main.py")
        
        return True

def main():
    """Main entry point"""
    try:
        setup = BotSetup()
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
