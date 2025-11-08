"""
Tests for game bridge functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psutil

from SRC.game.source_bridge import SourceBridge, ConnectionType


class TestSourceBridge:
    """Test Source Engine bridge functionality."""
    
    @patch('SRC.game.source_bridge.telnetlib')
    @patch('SRC.game.source_bridge.psutil')
    def test_source_bridge_creation(self, mock_psutil, mock_telnetlib):
        """Test SourceBridge creation and initialization."""
        # Mock successful NetCon connection
        mock_telnet = Mock()
        mock_telnetlib.Telnet.return_value = mock_telnet
        
        bridge = SourceBridge("127.0.0.1", 2121)
        
        assert bridge.netcon_host == "127.0.0.1"
        assert bridge.netcon_port == 2121
        assert bridge.connection_type == ConnectionType.NETCON
        assert bridge._is_connected
        mock_telnetlib.Telnet.assert_called_once_with("127.0.0.1", 2121, timeout=5)
    
    @patch('SRC.game.source_bridge.telnetlib')
    @patch('SRC.game.source_bridge.psutil')
    def test_netcon_connection_failure_fallback_to_hijack(self, mock_psutil, mock_telnetlib):
        """Test fallback to hijack when NetCon fails."""
        # Mock NetCon failure
        mock_telnetlib.Telnet.side_effect = ConnectionRefusedError()
        
        # Mock successful process finding
        mock_process = Mock()
        mock_process.info = {'name': 'hl2.exe'}
        mock_psutil.process_iter.return_value = [mock_process]
        
        bridge = SourceBridge()
        
        assert bridge.connection_type == ConnectionType.HIJACK
        assert bridge.game_process == mock_process
        assert bridge._is_connected
    
    @patch('SRC.game.source_bridge.telnetlib')
    @patch('SRC.game.source_bridge.psutil')
    def test_no_connection_available(self, mock_psutil, mock_telnetlib):
        """Test when no connection method is available."""
        # Mock NetCon failure
        mock_telnetlib.Telnet.side_effect = ConnectionRefusedError()
        
        # Mock no game processes found
        mock_psutil.process_iter.return_value = []
        
        bridge = SourceBridge()
        
        assert bridge.connection_type == ConnectionType.NONE
        assert not bridge._is_connected
    
    def test_find_game_process(self, mock_process):
        """Test finding Source Engine game processes."""
        with patch('SRC.game.source_bridge.psutil') as mock_psutil:
            # Mock process with Source Engine game
            mock_process.info = {'name': 'hl2.exe'}
            mock_psutil.process_iter.return_value = [mock_process]
            
            bridge = SourceBridge.__new__(SourceBridge)  # Create without __init__
            bridge.logger = Mock()
            bridge.game_process = None
            
            found_process = bridge._find_game_process()
            
            assert found_process == mock_process
    
    def test_find_game_process_no_games(self):
        """Test finding game processes when none exist."""
        with patch('SRC.game.source_bridge.psutil') as mock_psutil:
            # Mock no Source Engine games
            mock_other_process = Mock()
            mock_other_process.info = {'name': 'notepad.exe'}
            mock_psutil.process_iter.return_value = [mock_other_process]
            
            bridge = SourceBridge.__new__(SourceBridge)
            bridge.logger = Mock()
            bridge.game_process = None
            
            found_process = bridge._find_game_process()
            
            assert found_process is None
    
    @patch('SRC.game.source_bridge.psutil', None)
    def test_find_game_process_no_psutil(self):
        """Test finding game processes when psutil is not available."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.logger = Mock()
        bridge.game_process = None
        
        found_process = bridge._find_game_process()
        
        assert found_process is None


class TestSourceBridgeNetCon:
    """Test NetCon-specific functionality."""
    
    def test_netcon_send_single_command(self, mock_telnet):
        """Test sending single command via NetCon."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.logger = Mock()
        bridge.telnet_connection = mock_telnet
        bridge.connection_type = ConnectionType.NETCON
        bridge._is_connected = True
        
        result = bridge._send_netcon_command("noclip")
        
        assert result
        mock_telnet.write.assert_called_once_with(b"noclip\n")
    
    def test_netcon_send_multiple_commands(self, mock_telnet):
        """Test sending multiple commands via NetCon."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.logger = Mock()
        bridge.telnet_connection = mock_telnet
        bridge.connection_type = ConnectionType.NETCON
        bridge._is_connected = True
        
        commands = ["noclip", "god", "notarget"]
        result = bridge._send_netcon_command(commands)
        
        assert result
        mock_telnet.write.assert_called_once_with(b"noclip;god;notarget\n")
    
    def test_netcon_send_command_failure(self, mock_telnet):
        """Test NetCon command sending failure."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.telnet_connection = mock_telnet
        bridge.connection_type = ConnectionType.NETCON
        bridge._is_connected = True
        bridge.logger = Mock()
        
        mock_telnet.write.side_effect = OSError("Connection lost")
        
        result = bridge._send_netcon_command("noclip")
        
        assert not result
    
    def test_netcon_is_valid(self, mock_telnet):
        """Test NetCon connection validity check."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.logger = Mock()
        bridge.telnet_connection = mock_telnet
        bridge.connection_type = ConnectionType.NETCON
        bridge._is_connected = True
        
        # Test valid connection
        mock_telnet.read_very_eager.return_value = b""
        assert bridge._is_netcon_valid()
        
        # Test invalid connection
        mock_telnet.read_very_eager.side_effect = EOFError()
        assert not bridge._is_netcon_valid()
        assert bridge.telnet_connection is None


class TestSourceBridgeHijack:
    """Test hijack-specific functionality."""
    
    @patch('SRC.game.source_bridge.subprocess')
    def test_hijack_send_single_command(self, mock_subprocess, mock_process):
        """Test sending single command via hijack."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.game_process = mock_process
        bridge.connection_type = ConnectionType.HIJACK
        bridge._is_connected = True
        bridge.logger = Mock()
        
        mock_process.exe.return_value = "C:\\Games\\HL2\\hl2.exe"
        
        result = bridge._send_hijack_command("noclip")
        
        assert result
        expected_params = ["C:\\Games\\HL2\\hl2.exe", "-hijack", "+noclip"]
        mock_subprocess.Popen.assert_called_once()
        args, kwargs = mock_subprocess.Popen.call_args
        assert args[0] == expected_params
    
    @patch('SRC.game.source_bridge.subprocess')
    def test_hijack_send_multiple_commands(self, mock_subprocess, mock_process):
        """Test sending multiple commands via hijack."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.game_process = mock_process
        bridge.connection_type = ConnectionType.HIJACK
        bridge._is_connected = True
        bridge.logger = Mock()
        
        mock_process.exe.return_value = "C:\\Games\\HL2\\hl2.exe"
        
        commands = ["noclip", "god"]
        result = bridge._send_hijack_command(commands)
        
        assert result
        expected_params = ["C:\\Games\\HL2\\hl2.exe", "-hijack", "+noclip", "+god"]
        mock_subprocess.Popen.assert_called_once()
        args, kwargs = mock_subprocess.Popen.call_args
        assert args[0] == expected_params
    
    @patch('SRC.game.source_bridge.subprocess')
    def test_hijack_send_command_failure(self, mock_subprocess, mock_process):
        """Test hijack command sending failure."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.game_process = mock_process
        bridge.connection_type = ConnectionType.HIJACK
        bridge._is_connected = True
        bridge.logger = Mock()
        
        mock_process.exe.side_effect = OSError("Process not accessible")
        
        result = bridge._send_hijack_command("noclip")
        
        assert not result
    
    def test_hijack_is_valid(self, mock_process):
        """Test hijack connection validity check."""
        bridge = SourceBridge.__new__(SourceBridge)
        bridge.logger = Mock()
        bridge.game_process = mock_process
        bridge.connection_type = ConnectionType.HIJACK
        bridge._is_connected = True
        
        # Test valid process
        mock_process.is_running.return_value = True
        assert bridge._is_hijack_valid()
        
        # Test invalid process
        mock_process.is_running.side_effect = psutil.NoSuchProcess(mock_process.pid)
        assert not bridge._is_hijack_valid()
        assert bridge.game_process is None


class TestSourceBridgeGeneral:
    """Test general SourceBridge functionality."""

    @pytest.fixture
    def bridge(self):
        with patch('SRC.game.source_bridge.SourceBridge.connect') as mock_connect:
            bridge = SourceBridge()
            mock_connect.reset_mock()
            yield bridge

    def test_send_command_with_reconnect(self, bridge):
        """Test sending command with automatic reconnection."""
        with patch.object(bridge, 'is_valid', side_effect=[False, True]):
            bridge.connect.return_value = True
            bridge._send_netcon_command = Mock(return_value=True)
            bridge.connection_type = ConnectionType.NETCON

            # Un-mock send_command to test the real logic
            bridge.send_command = SourceBridge.send_command.__get__(bridge)

            result = bridge.send_command("noclip")

            assert result
            bridge.connect.assert_called_once()
            bridge._send_netcon_command.assert_called_once_with("noclip")

    def test_execute_commands_empty_list(self, bridge):
        """Test executing empty command list."""
        bridge.send_command = Mock()
        result = bridge.execute_commands([])
        assert result
        bridge.send_command.assert_not_called()

    def test_execute_commands_with_list(self, bridge):
        """Test executing list of commands."""
        bridge.send_command = Mock()
        commands = ["noclip", "god", "notarget"]
        result = bridge.execute_commands(commands)
        assert result
        bridge.send_command.assert_called_once_with(commands)
    
    def test_get_connection_info_netcon(self, mock_telnet):
        """Test getting connection info for NetCon."""
        with patch('SRC.game.source_bridge.SourceBridge.connect'):
            bridge = SourceBridge()
        bridge.logger = Mock()
        bridge._is_connected = True
        bridge.connection_type = ConnectionType.NETCON
        bridge.netcon_host = "127.0.0.1"
        bridge.netcon_port = 2121
        bridge.telnet_connection = mock_telnet
        bridge.game_process = None
        
        with patch.object(bridge, 'is_valid', return_value=True):
            info = bridge.get_connection_info()
        
        assert info["connected"]
        assert info["connection_type"] == "netcon"
        assert info["netcon_host"] == "127.0.0.1"
        assert info["netcon_port"] == 2121
    
    def test_get_connection_info_hijack(self, mock_process):
        """Test getting connection info for hijack."""
        with patch('SRC.game.source_bridge.SourceBridge.connect'):
            bridge = SourceBridge()
        bridge.logger = Mock()
        bridge._is_connected = True
        bridge.connection_type = ConnectionType.HIJACK
        bridge.telnet_connection = None
        bridge.game_process = mock_process
        
        mock_process.name.return_value = "hl2.exe"
        mock_process.pid = 1234
        
        with patch.object(bridge, 'is_valid', return_value=True):
            info = bridge.get_connection_info()
        
        assert info["connected"]
        assert info["connection_type"] == "hijack"
        assert info["game_name"] == "hl2.exe"
        assert info["game_pid"] == 1234
    
    def test_disconnect(self, mock_telnet, mock_process):
        """Test disconnection cleanup."""
        with patch('SRC.game.source_bridge.SourceBridge.connect'):
            bridge = SourceBridge()
        bridge.telnet_connection = mock_telnet
        bridge.game_process = mock_process
        bridge.connection_type = ConnectionType.NETCON
        bridge._is_connected = True
        bridge.logger = Mock()
        
        bridge.disconnect()
        
        mock_telnet.close.assert_called_once()
        assert bridge.telnet_connection is None
        assert bridge.game_process is None
        assert bridge.connection_type == ConnectionType.NONE
        assert not bridge._is_connected

