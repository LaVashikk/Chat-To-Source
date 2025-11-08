"""
Utility functions and configuration management for Chat2Source.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import toml
except ImportError:
    toml = None

try:
    import json
except ImportError:
    json = None


class ConfigManager:
    """Configuration manager for handling TOML and JSON config files."""
    
    def __init__(self, settings_file: str = "settings.toml", forbidden_file: str = "forbidden_config.toml"):
        self.settings_file = settings_file
        self.forbidden_file = forbidden_file
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration data
        self.settings: Dict[str, Any] = {}
        self.forbidden_config: Dict[str, Any] = {}
        
        # Load configurations
        self.load_configs()
    
    def load_configs(self):
        """Load all configuration files."""
        self.settings = self._load_config_file(self.settings_file)
        self.forbidden_config = self._load_config_file(self.forbidden_file)
        
        if not self.settings:
            self.logger.warning(f"Settings file {self.settings_file} not found or empty, using defaults")
            self.settings = self._get_default_settings()
        
        if not self.forbidden_config:
            self.logger.warning(f"Forbidden config file {self.forbidden_file} not found or empty, using defaults")
            self.forbidden_config = self._get_default_forbidden_config()
    
    def _load_config_file(self, filename: str) -> Dict[str, Any]:
        """Load a configuration file (TOML or JSON)."""
        if not os.path.exists(filename):
            self.logger.debug(f"Config file {filename} not found")
            return {}
        
        try:
            file_path = Path(filename)
            
            if file_path.suffix.lower() == '.toml':
                if toml is None:
                    self.logger.error("toml package not available. Install with: pip install toml")
                    return {}
                
                with open(filename, 'r', encoding='utf-8') as f:
                    return toml.load(f)
            
            elif file_path.suffix.lower() == '.json':
                if json is None:
                    self.logger.error("json package not available")
                    return {}
                
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            else:
                self.logger.error(f"Unsupported config file format: {filename}")
                return {}
        
        except Exception as e:
            self.logger.error(f"Error loading config file {filename}: {e}")
            return {}
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings configuration."""
        return {
            "stream": {
                "platform": "youtube",
                "url": "",
                "update_interval": 1.0
            },
            "widget": {
                "host": "127.0.0.1",
                "port": 5000,
                "debug": False
            },
            "game": {
                "netcon_host": "127.0.0.1",
                "netcon_port": 2121,
                "auto_reconnect": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def _get_default_forbidden_config(self) -> Dict[str, Any]:
        """Get default forbidden configuration."""
        return {
            "commands": [
                "quit", "exit", "disconnect", "retry", "changelevel",
                "map", "restart", "sv_cheats", "rcon", "status"
            ],
            "entities": [
                "func_breakable", "trigger_hurt", "env_explosion",
                "point_hurt", "game_end"
            ],
            "scripts": [
                "exec", "alias", "bind", "unbind", "unbindall"
            ],
            "script_exceptions": [
                "exec autoexec.cfg", "exec config.cfg"
            ],
            "cvar_limits": {
                "enable_filter": True,
                "default_max": 100,
                "individual_max": {
                    "sv_gravity": 800,
                    "host_timescale": 1,
                    "sv_airaccelerate": 10
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value using dot notation."""
        return self._get_nested_value(self.settings, key, default)
    
    def get_forbidden_commands(self) -> List[str]:
        """Get list of forbidden commands."""
        return self.forbidden_config.get("commands", [])
    
    def get_forbidden_entities(self) -> List[str]:
        """Get list of forbidden entities."""
        return self.forbidden_config.get("entities", [])
    
    def get_forbidden_scripts(self) -> List[str]:
        """Get list of forbidden scripts."""
        return self.forbidden_config.get("scripts", [])
    
    def get_script_exceptions(self) -> List[str]:
        """Get list of script exceptions."""
        return self.forbidden_config.get("script_exceptions", [])
    
    def get_cvar_limits(self) -> Dict[str, Any]:
        """Get cvar limits configuration."""
        return self.forbidden_config.get("cvar_limits", {})
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """Set a setting value using dot notation."""
        self._set_nested_value(self.settings, key, value)
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """Set nested dictionary value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save_settings(self, filename: Optional[str] = None):
        """Save settings to file."""
        if filename is None:
            filename = self.settings_file
        
        self._save_config_file(filename, self.settings)
    
    def save_forbidden_config(self, filename: Optional[str] = None):
        """Save forbidden config to file."""
        if filename is None:
            filename = self.forbidden_file
        
        self._save_config_file(filename, self.forbidden_config)
    
    def _save_config_file(self, filename: str, data: Dict[str, Any]):
        """Save configuration data to file."""
        try:
            file_path = Path(filename)
            
            if file_path.suffix.lower() == '.toml':
                if toml is None:
                    self.logger.error("toml package not available")
                    return
                
                with open(filename, 'w', encoding='utf-8') as f:
                    toml.dump(data, f)
            
            elif file_path.suffix.lower() == '.json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            else:
                self.logger.error(f"Unsupported config file format: {filename}")
        
        except Exception as e:
            self.logger.error(f"Error saving config file {filename}: {e}")
    
    def reload(self):
        """Reload all configuration files."""
        self.load_configs()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy()
    
    def get_all_forbidden_config(self) -> Dict[str, Any]:
        """Get all forbidden configuration."""
        return self.forbidden_config.copy()


def setup_logging(config: ConfigManager):
    """Setup logging configuration."""
    level = config.get("logging.level", "INFO")
    format_str = config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=format_str,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('chat2source.log', encoding='utf-8')
        ]
    )


def validate_stream_url(url: str, platform: str) -> bool:
    """Validate stream URL format."""
    if not url:
        return False
    
    platform = platform.lower()
    
    if platform == "youtube":
        # YouTube video ID validation
        if len(url) == 11 and url.isalnum():
            return True
        # YouTube URL validation
        youtube_patterns = [
            "youtube.com/watch?v=",
            "youtu.be/",
            "youtube.com/live/"
        ]
        return any(pattern in url for pattern in youtube_patterns)
    
    elif platform == "twitch":
        # Twitch channel name validation
        if url.startswith("#"):
            url = url[1:]  # Remove # prefix
        return url.isalnum() and len(url) > 0
    
    return False


def extract_stream_identifier(url: str, platform: str) -> Optional[str]:
    """Extract stream identifier from URL."""
    if not validate_stream_url(url, platform):
        return None
    
    platform = platform.lower()
    
    if platform == "youtube":
        # Extract video ID from various YouTube URL formats
        if len(url) == 11 and url.isalnum():
            return url
        
        if "youtube.com/watch?v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/live/" in url:
            return url.split("live/")[1].split("?")[0]
    
    elif platform == "twitch":
        # Extract channel name
        if url.startswith("#"):
            return url[1:]
        return url
    
    return None


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def ensure_directory(path: Union[str, Path]):
    """Ensure directory exists, create if it doesn't."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

