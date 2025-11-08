"""
Tests for utility functions and configuration management.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from SRC.utils import (
    ConfigManager, setup_logging, validate_stream_url, 
    extract_stream_identifier, format_duration, sanitize_filename, ensure_directory
)


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def test_config_manager_creation(self, mock_config):
        """Test ConfigManager creation with existing files."""
        assert mock_config.settings is not None
        assert mock_config.forbidden_config is not None
        assert mock_config.get("stream.platform") == "youtube"
    
    def test_config_manager_missing_files(self, temp_config_dir):
        """Test ConfigManager with missing config files."""
        settings_file = os.path.join(temp_config_dir, "missing_settings.toml")
        forbidden_file = os.path.join(temp_config_dir, "missing_forbidden.toml")
        
        config = ConfigManager(settings_file, forbidden_file)
        
        # Should use defaults
        assert config.settings is not None
        assert config.forbidden_config is not None
        assert config.get("stream.platform") == "youtube"  # Default value
    
    def test_get_nested_value(self, mock_config):
        """Test getting nested configuration values."""
        assert mock_config.get("stream.platform") == "youtube"
        assert mock_config.get("widget.port") == 5001
        assert mock_config.get("nonexistent.key", "default") == "default"
    
    def test_set_nested_value(self, mock_config):
        """Test setting nested configuration values."""
        mock_config.set("stream.new_setting", "test_value")
        assert mock_config.get("stream.new_setting") == "test_value"
        
        mock_config.set("new_section.new_key", 42)
        assert mock_config.get("new_section.new_key") == 42
    
    def test_get_forbidden_commands(self, mock_config):
        """Test getting forbidden commands list."""
        commands = mock_config.get_forbidden_commands()
        assert isinstance(commands, list)
        assert "quit" in commands
        assert "sv_cheats" in commands
    
    def test_get_forbidden_entities(self, mock_config):
        """Test getting forbidden entities list."""
        entities = mock_config.get_forbidden_entities()
        assert isinstance(entities, list)
        assert "trigger_hurt" in entities
    
    def test_get_forbidden_scripts(self, mock_config):
        """Test getting forbidden scripts list."""
        scripts = mock_config.get_forbidden_scripts()
        assert isinstance(scripts, list)
        assert "exec" in scripts
    
    def test_get_script_exceptions(self, mock_config):
        """Test getting script exceptions list."""
        exceptions = mock_config.get_script_exceptions()
        assert isinstance(exceptions, list)
        assert "exec autoexec.cfg" in exceptions
    
    def test_get_cvar_limits(self, mock_config):
        """Test getting cvar limits configuration."""
        limits = mock_config.get_cvar_limits()
        assert isinstance(limits, dict)
        assert limits["enable_filter"] is True
        assert limits["default_max"] == 50
        assert limits["individual_max"]["sv_gravity"] == 400
    
    @patch('SRC.utils.toml')
    def test_save_settings(self, mock_toml, mock_config, temp_config_dir):
        """Test saving settings to file."""
        test_file = os.path.join(temp_config_dir, "test_save.toml")
        
        mock_config.save_settings(test_file)
        
        mock_toml.dump.assert_called_once()
    
    def test_reload_configs(self, mock_config):
        """Test reloading configuration files."""
        original_platform = mock_config.get("stream.platform")
        
        # Modify in memory
        mock_config.set("stream.platform", "twitch")
        assert mock_config.get("stream.platform") == "twitch"
        
        # Reload should restore original
        mock_config.reload()
        assert mock_config.get("stream.platform") == original_platform
    
    @patch('SRC.utils.toml', None)
    def test_load_toml_without_toml_package(self, temp_config_dir):
        """Test loading TOML files when toml package is not available."""
        settings_file = os.path.join(temp_config_dir, "test.toml")
        
        with open(settings_file, 'w') as f:
            f.write('[test]\nkey = "value"')
        
        config = ConfigManager(settings_file, "nonexistent.toml")
        
        # Should fall back to defaults since toml is not available
        assert config.settings != {}  # Should have defaults
    
    def test_load_json_config(self, temp_config_dir):
        """Test loading JSON configuration files."""
        json_file = os.path.join(temp_config_dir, "test.json")
        
        with open(json_file, 'w') as f:
            f.write('{"test": {"key": "value"}}')
        
        config = ConfigManager.__new__(ConfigManager)
        result = config._load_config_file(json_file)
        
        assert result["test"]["key"] == "value"
    
    def test_load_unsupported_format(self, temp_config_dir):
        """Test loading unsupported file format."""
        txt_file = os.path.join(temp_config_dir, "test.txt")
        
        with open(txt_file, 'w') as f:
            f.write("some text")
        
        config = ConfigManager.__new__(ConfigManager)
        config.logger = Mock()
        result = config._load_config_file(txt_file)
        
        assert result == {}


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_validate_stream_url_youtube(self):
        """Test YouTube URL validation."""
        # Valid YouTube URLs
        assert validate_stream_url("dQw4w9WgXcQ", "youtube")
        assert validate_stream_url("https://youtube.com/watch?v=dQw4w9WgXcQ", "youtube")
        assert validate_stream_url("https://youtu.be/dQw4w9WgXcQ", "youtube")
        assert validate_stream_url("https://youtube.com/live/dQw4w9WgXcQ", "youtube")
        
        # Invalid YouTube URLs
        assert not validate_stream_url("", "youtube")
        assert not validate_stream_url("invalid", "youtube")
        assert not validate_stream_url("https://example.com", "youtube")
    
    def test_validate_stream_url_twitch(self):
        """Test Twitch URL validation."""
        # Valid Twitch channels
        assert validate_stream_url("testchannel", "twitch")
        assert validate_stream_url("#testchannel", "twitch")
        assert validate_stream_url("TestChannel123", "twitch")
        
        # Invalid Twitch channels
        assert not validate_stream_url("", "twitch")
        assert not validate_stream_url("test channel", "twitch")  # Spaces not allowed
        assert not validate_stream_url("test@channel", "twitch")  # Special chars not allowed
    
    def test_validate_stream_url_invalid_platform(self):
        """Test URL validation with invalid platform."""
        assert not validate_stream_url("anything", "invalid_platform")
    
    def test_extract_stream_identifier_youtube(self):
        """Test extracting YouTube video IDs."""
        # Direct video ID
        assert extract_stream_identifier("dQw4w9WgXcQ", "youtube") == "dQw4w9WgXcQ"
        
        # YouTube watch URL
        assert extract_stream_identifier("https://youtube.com/watch?v=dQw4w9WgXcQ", "youtube") == "dQw4w9WgXcQ"
        
        # YouTube short URL
        assert extract_stream_identifier("https://youtu.be/dQw4w9WgXcQ", "youtube") == "dQw4w9WgXcQ"
        
        # YouTube live URL
        assert extract_stream_identifier("https://youtube.com/live/dQw4w9WgXcQ", "youtube") == "dQw4w9WgXcQ"
        
        # Invalid URL
        assert extract_stream_identifier("invalid", "youtube") is None
    
    def test_extract_stream_identifier_twitch(self):
        """Test extracting Twitch channel names."""
        # Channel name
        assert extract_stream_identifier("testchannel", "twitch") == "testchannel"
        
        # Channel name with #
        assert extract_stream_identifier("#testchannel", "twitch") == "testchannel"
        
        # Invalid channel
        assert extract_stream_identifier("", "twitch") is None
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(30.5) == "30.5s"
        assert format_duration(90) == "1.5m"
        assert format_duration(3600) == "1.0h"
        assert format_duration(7200) == "2.0h"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
        assert sanitize_filename("file<with>bad:chars") == "file_with_bad_chars"
        assert sanitize_filename("  file with spaces  ") == "file with spaces"
        assert sanitize_filename("file.with.dots.") == "file.with.dots"
        
        # Test long filename
        long_name = "a" * 300
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
    
    def test_ensure_directory(self, temp_config_dir):
        """Test directory creation."""
        test_dir = os.path.join(temp_config_dir, "test", "nested", "directory")
        
        ensure_directory(test_dir)
        
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)
        
        # Test with existing directory
        ensure_directory(test_dir)  # Should not raise error
        assert os.path.exists(test_dir)


class TestLoggingSetup:
    """Test logging configuration."""
    
    def test_setup_logging_default(self, mock_config):
        """Test logging setup with default configuration."""
        with patch('SRC.utils.logging') as mock_logging:
            setup_logging(mock_config)
            
            mock_logging.basicConfig.assert_called_once()
            args, kwargs = mock_logging.basicConfig.call_args
            assert kwargs['level'] == mock_logging.DEBUG  # From config
    
    def test_setup_logging_custom_level(self, mock_config):
        """Test logging setup with custom level."""
        mock_config.set("logging.level", "WARNING")
        
        with patch('SRC.utils.logging') as mock_logging:
            setup_logging(mock_config)
            
            mock_logging.basicConfig.assert_called_once()
            args, kwargs = mock_logging.basicConfig.call_args
            assert kwargs['level'] == mock_logging.WARNING
    
    def test_setup_logging_invalid_level(self, mock_config):
        """Test logging setup with invalid level."""
        mock_config.set("logging.level", "INVALID")

        with patch('SRC.utils.logging', spec=True) as mock_logging:
            setup_logging(mock_config)

            mock_logging.basicConfig.assert_called_once()
            args, kwargs = mock_logging.basicConfig.call_args
            assert kwargs['level'] == mock_logging.INFO  # Default fallback

