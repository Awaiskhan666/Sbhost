"""
Configuration Management System for LTC Flash Discord Selfbot
Provides centralized configuration, settings persistence, and environment management
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.config_path = Path(config_file)
        self.default_config = self._get_default_config()
        self.config = self._load_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            "bot": {
                "command_prefix": "-",
                "case_insensitive": True,
                "owner_id": None,  # Set dynamically from bot.user.id after login
                "zero_error_mode": False,
                "ultra_fast_startup": True,
                "low_latency_mode": True
            },
            "security": {
                "anti_ban_enabled": True,
                "response_delay_min": 0.3,
                "response_delay_max": 0.8,
                "owner_max_speed": True,
                "failed_attempts_limit": 3,
                "lockout_duration_minutes": 15,
                "session_timeout_minutes": 30,
                "command_rate_limit": 10,
                "presence_rotation_enabled": True,
                "presence_rotation_interval_min": 10,
                "presence_rotation_interval_max": 15
            },
            "features": {
                "afk_system_enabled": True,
                "auto_nigga_detection": True,
                "enhanced_keep_alive": True,
                "database_logging": True,
                "console_capture": True,
                "analytics_enabled": True
            },
            "performance": {
                "jija_ultra_fast_mode": True,
                "jija_min_delay": 0.02,
                "jija_max_delay": 1.0,
                "jija_variations_count": 20,
                "jija_burst_mode": True,
                "console_log_max_entries": 100,
                "keep_alive_interval": 30
            },
            "limits": {
                "spam_daily_limit": 50,
                "drown_daily_limit": 30,
                "debate_daily_limit": 25,
                "flash_daily_limit": 100,
                "max_targets": 50,
                "max_gc_spam_targets": 10
            },
            "database": {
                "enabled": True,
                "url": os.environ.get("DATABASE_URL", "sqlite:///bot_data.db"),
                "pool_recycle": 300,
                "pool_pre_ping": True,
                "auto_create_tables": True
            },
            "web": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 5000,
                "debug": True,
                "secret_key": os.environ.get("SESSION_SECRET", "dev_key_change_in_production"),
                "analytics_enabled": True,
                "real_time_logs": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "console_output": True,
                "file_output": False,
                "max_log_files": 5,
                "max_log_size_mb": 10
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(self.default_config, loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
                return self.default_config.copy()
        else:
            # Create default config file
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_config(self, config: Optional[Dict] = None):
        """Save current configuration to file"""
        config_to_save = config or self.config
        config_to_save["_last_updated"] = datetime.utcnow().isoformat()
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'bot.owner_id')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        if save:
            self.save_config()
    
    def update_section(self, section: str, values: Dict[str, Any], save: bool = True):
        """Update an entire configuration section"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(values)
        
        if save:
            self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        self.save_config()
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        overrides = {}
        
        # Bot configuration from environment
        if os.environ.get("OWNER_ID"):
            overrides["bot.owner_id"] = int(os.environ["OWNER_ID"])
        
        if os.environ.get("COMMAND_PREFIX"):
            overrides["bot.command_prefix"] = os.environ["COMMAND_PREFIX"]
        
        # Database configuration
        if os.environ.get("DATABASE_URL"):
            overrides["database.url"] = os.environ["DATABASE_URL"]
        
        # Web configuration
        if os.environ.get("PORT"):
            overrides["web.port"] = int(os.environ["PORT"])
        
        if os.environ.get("SESSION_SECRET"):
            overrides["web.secret_key"] = os.environ["SESSION_SECRET"]
        
        # Security configuration
        if os.environ.get("ANTI_BAN_ENABLED"):
            overrides["security.anti_ban_enabled"] = os.environ["ANTI_BAN_ENABLED"].lower() == "true"
        
        return overrides
    
    def apply_environment_overrides(self):
        """Apply environment variable overrides to configuration"""
        overrides = self.get_environment_overrides()
        for key_path, value in overrides.items():
            self.set(key_path, value, save=False)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate owner ID
        if not isinstance(self.get("bot.owner_id"), int):
            issues.append("bot.owner_id must be an integer")
        
        # Validate delays
        min_delay = self.get("security.response_delay_min")
        max_delay = self.get("security.response_delay_max")
        if min_delay >= max_delay:
            issues.append("security.response_delay_min must be less than response_delay_max")
        
        # Validate database URL
        db_url = self.get("database.url")
        if not db_url or not isinstance(db_url, str):
            issues.append("database.url must be a valid string")
        
        # Validate port
        port = self.get("web.port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            issues.append("web.port must be an integer between 1 and 65535")
        
        return issues
    
    def export_config(self, format: str = "json") -> str:
        """Export configuration in specified format"""
        if format.lower() == "yaml":
            return yaml.dump(self.config, default_flow_style=False, indent=2)
        elif format.lower() == "json":
            return json.dumps(self.config, indent=2)
        else:
            raise ValueError("Unsupported format. Use 'json' or 'yaml'")
    
    def import_config(self, config_data: str, format: str = "json"):
        """Import configuration from string"""
        try:
            if format.lower() == "yaml":
                new_config = yaml.safe_load(config_data)
            elif format.lower() == "json":
                new_config = json.loads(config_data)
            else:
                raise ValueError("Unsupported format. Use 'json' or 'yaml'")
            
            # Validate and merge with defaults
            self.config = self._merge_configs(self.default_config, new_config)
            self.save_config()
            return True
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

# Global configuration manager instance
config_manager = ConfigManager()

# Convenience functions for common operations
def get_config(key_path: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config_manager.get(key_path, default)

def set_config(key_path: str, value: Any, save: bool = True):
    """Set configuration value"""
    config_manager.set(key_path, value, save)

def reload_config():
    """Reload configuration from file"""
    global config_manager
    config_manager = ConfigManager()
    return config_manager

def get_bot_config() -> Dict[str, Any]:
    """Get bot-specific configuration"""
    return config_manager.get("bot", {})

def get_security_config() -> Dict[str, Any]:
    """Get security-specific configuration"""
    return config_manager.get("security", {})

def get_database_config() -> Dict[str, Any]:
    """Get database-specific configuration"""
    return config_manager.get("database", {})

def get_web_config() -> Dict[str, Any]:
    """Get web-specific configuration"""
    return config_manager.get("web", {})

# Initialize configuration on import
config_manager.apply_environment_overrides()
validation_issues = config_manager.validate_config()
if validation_issues:
    print(f"⚠️ Configuration validation issues: {', '.join(validation_issues)}")
else:
    print("✅ Configuration loaded and validated successfully")