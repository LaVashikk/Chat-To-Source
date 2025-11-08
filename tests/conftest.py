"""
Pytest configuration and fixtures for Chat2Source tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

from SRC.utils import ConfigManager
from SRC.chat.chat_manager import ChatMessage, ChatAuthor
from SRC.game.source_bridge import SourceBridge


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_config(temp_config_dir):
    """Create a mock configuration manager with test data."""
    settings_file = os.path.join(temp_config_dir, "test_settings.toml")
    forbidden_file = os.path.join(temp_config_dir, "test_forbidden.toml")
    
    # Create test config files
    with open(settings_file, 'w') as f:
        f.write("""
[stream]
platform = "youtube"
url = "test_video_id"
update_interval = 0.1

[widget]
host = "127.0.0.1"
port = 5001
debug = true

[game]
netcon_host = "127.0.0.1"
netcon_port = 2121
auto_reconnect = false

[logging]
level = "DEBUG"
""")
    
    with open(forbidden_file, 'w') as f:
        f.write("""
commands = ["quit", "exit", "sv_cheats"]
entities = ["trigger_hurt", "env_explosion"]
scripts = ["exec", "alias"]
script_exceptions = ["exec autoexec.cfg"]

[cvar_limits]
enable_filter = true
default_max = 50

[cvar_limits.individual_max]
sv_gravity = 400
""")
    
    return ConfigManager(settings_file, forbidden_file)


@pytest.fixture
def sample_chat_message():
    """Create a sample chat message for testing."""
    author = ChatAuthor(name="TestUser", image_url="https://example.com/avatar.jpg")
    return ChatMessage(
        author=author,
        message="!noclip +forward",
        timestamp="12:34:56"
    )


@pytest.fixture
def mock_youtube_chat():
    """Create a mock YouTube chat client."""
    mock_chat = Mock()
    mock_chat.is_valid.return_value = True
    mock_chat.get_messages.return_value = []
    mock_chat.disconnect = Mock()
    return mock_chat


@pytest.fixture
def mock_game_bridge():
    """Create a mock game bridge."""
    mock_bridge = Mock(spec=SourceBridge)
    mock_bridge.is_valid.return_value = True
    mock_bridge.send_command.return_value = True
    mock_bridge.execute_commands.return_value = True
    mock_bridge.get_connection_info.return_value = {
        "connected": True,
        "connection_type": "netcon",
        "valid": True
    }
    mock_bridge.disconnect = Mock()
    return mock_bridge


@pytest.fixture
def mock_widget():
    """Create a mock chat widget."""
    mock_widget = Mock()
    mock_widget.start_server.return_value = True
    mock_widget.is_running.return_value = True
    mock_widget.get_url.return_value = "http://127.0.0.1:5001"
    mock_widget.send_message = Mock()
    mock_widget.send_server_message = Mock()
    mock_widget.update_status = Mock()
    mock_widget.stop_server = Mock()
    return mock_widget


@pytest.fixture
def mock_telnet():
    """Create a mock telnet connection."""
    mock_telnet = Mock()
    mock_telnet.write = Mock()
    mock_telnet.read_very_eager = Mock(return_value=b"")
    mock_telnet.close = Mock()
    return mock_telnet


@pytest.fixture
def mock_process():
    """Create a mock process for game hijacking."""
    mock_process = Mock()
    mock_process.name.return_value = "hl2.exe"
    mock_process.pid = 1234
    mock_process.exe.return_value = "C:\\Games\\HL2\\hl2.exe"
    mock_process.is_running.return_value = True
    return mock_process


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Ensure we're in a clean state
    import logging
    logging.getLogger().handlers.clear()
    
    yield
    
    # Cleanup after test
    pass

