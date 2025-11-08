"""
Source Engine game bridge for sending commands via NetCon or process hijacking.
"""

import logging
import subprocess
import telnetlib
from enum import Enum
from typing import List, Optional, Union

try:
    import psutil
except ImportError:
    psutil = None


class ConnectionType(Enum):
    """Types of connections to Source Engine games."""
    NETCON = "netcon"
    HIJACK = "hijack"
    NONE = "none"


class SourceBridge:
    """Bridge for communicating with Source Engine games."""
    
    # Known Source Engine games
    SOURCE_ENGINE_GAMES = [
        "hl2", "csgo", "portal2", "chaos", "left4dead2", "bms",
        "tf2", "gmod", "css", "dods", "hl2dm", "portal", "ep1", "ep2"
    ]
    
    def __init__(self, netcon_host: str = "127.0.0.1", netcon_port: int = 2121):
        self.netcon_host = netcon_host
        self.netcon_port = netcon_port
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Connection state
        self.connection_type = ConnectionType.NONE
        self.telnet_connection: Optional[telnetlib.Telnet] = None
        self.game_process: Optional['psutil.Process'] = None
        self._is_connected = False
        
        # Attempt to connect
        self.connect()
    
    def connect(self) -> bool:
        """Attempt to connect to a Source Engine game."""
        self.logger.info("Attempting to connect to Source Engine game...")
        
        # Try NetCon first (preferred method)
        if self._connect_netcon():
            return True
        
        # Fall back to process hijacking
        if self._connect_hijack():
            return True
        
        self.logger.warning("Could not establish connection to any Source Engine game")
        return False
    
    def _connect_netcon(self) -> bool:
        """Connect via NetCon (telnet-based connection)."""
        try:
            self.logger.info(f"Attempting NetCon connection to {self.netcon_host}:{self.netcon_port}")
            self.telnet_connection = telnetlib.Telnet(self.netcon_host, self.netcon_port, timeout=5)
            self.connection_type = ConnectionType.NETCON
            self._is_connected = True
            self.logger.info("Successfully connected via NetCon")
            return True
        except (ConnectionRefusedError, OSError, Exception) as e:
            self.logger.debug(f"NetCon connection failed: {e}")
            self.telnet_connection = None
            return False
    
    def _connect_hijack(self) -> bool:
        """Connect via process hijacking."""
        if psutil is None:
            self.logger.error("psutil is not available. Install it with: pip install psutil")
            return False
        
        game_process = self._find_game_process()
        if game_process:
            self.game_process = game_process
            self.connection_type = ConnectionType.HIJACK
            self._is_connected = True
            self.logger.info(f"Successfully connected to {game_process.name()} via hijack")
            return True
        
        self.logger.debug("No Source Engine game process found")
        return False
    
    def _find_game_process(self) -> Optional['psutil.Process']:
        """Find a running Source Engine game process."""
        if psutil is None:
            return None
        
        try:
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    process_name = process.info['name'].lower()
                    if any(game in process_name for game in self.SOURCE_ENGINE_GAMES):
                        self.logger.debug(f"Found Source Engine game: {process.info['name']}")
                        return process
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error searching for game processes: {e}")
        
        return None
    
    def is_valid(self) -> bool:
        """Check if the connection is still valid."""
        if not self._is_connected:
            return False
        
        if self.connection_type == ConnectionType.NETCON:
            return self._is_netcon_valid()
        elif self.connection_type == ConnectionType.HIJACK:
            return self._is_hijack_valid()
        
        return False
    
    def _is_netcon_valid(self) -> bool:
        """Check if NetCon connection is still valid."""
        if not self.telnet_connection:
            return False
        
        try:
            # Try to read any pending data (non-blocking check)
            self.telnet_connection.read_very_eager()
            return True
        except (EOFError, OSError, Exception):
            self.logger.warning("NetCon connection lost")
            self.telnet_connection = None
            self._is_connected = False
            return False
    
    def _is_hijack_valid(self) -> bool:
        """Check if hijack connection is still valid."""
        if not self.game_process:
            return False
        
        try:
            return self.game_process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.logger.warning("Game process no longer accessible")
            self.game_process = None
            self._is_connected = False
            return False
    
    def send_command(self, command: Union[str, List[str]]) -> bool:
        """Send a command or list of commands to the game."""
        if not self.is_valid():
            self.logger.warning("Connection invalid, attempting to reconnect...")
            if not self.connect():
                self.logger.error("Failed to reconnect to game")
                return False
        
        if self.connection_type == ConnectionType.NETCON:
            return self._send_netcon_command(command)
        elif self.connection_type == ConnectionType.HIJACK:
            return self._send_hijack_command(command)
        
        return False
    
    def _send_netcon_command(self, command: Union[str, List[str]]) -> bool:
        """Send command via NetCon."""
        if not self.telnet_connection:
            return False
        
        try:
            if isinstance(command, list):
                command_str = ";".join(command)
            else:
                command_str = command
            
            self.logger.debug(f"Sending NetCon command: {command_str}")
            self.telnet_connection.write(f"{command_str}\n".encode("utf-8"))
            return True
        except (OSError, Exception) as e:
            self.logger.error(f"Failed to send NetCon command: {e}")
            return False
    
    def _send_hijack_command(self, command: Union[str, List[str]]) -> bool:
        """Send command via process hijacking."""
        if not self.game_process:
            return False
        
        try:
            # Build command line arguments
            params = [self.game_process.exe(), "-hijack"]
            
            if isinstance(command, list):
                for cmd in command:
                    params.append(f"+{cmd}")
            else:
                params.append(f"+{command}")
            
            self.logger.debug(f"Sending hijack command: {params}")
            
            # Execute the hijack command
            subprocess.Popen(
                params,
                creationflags=subprocess.DETACHED_PROCESS if hasattr(subprocess, 'DETACHED_PROCESS') else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (OSError, Exception) as e:
            self.logger.error(f"Failed to send hijack command: {e}")
            return False
    
    def execute_commands(self, commands: List[str]) -> bool:
        """Execute a list of commands."""
        if not commands:
            return True
        
        self.logger.info(f"Executing {len(commands)} commands")
        return self.send_command(commands)
    
    def disconnect(self):
        """Disconnect from the game."""
        self.logger.info("Disconnecting from game")
        
        if self.telnet_connection:
            try:
                self.telnet_connection.close()
            except Exception:
                pass
            self.telnet_connection = None
        
        self.game_process = None
        self.connection_type = ConnectionType.NONE
        self._is_connected = False
    
    def get_connection_info(self) -> dict:
        """Get information about the current connection."""
        info = {
            "connected": self._is_connected,
            "connection_type": self.connection_type.value,
            "valid": self.is_valid()
        }
        
        if self.connection_type == ConnectionType.NETCON:
            info["netcon_host"] = self.netcon_host
            info["netcon_port"] = self.netcon_port
        elif self.connection_type == ConnectionType.HIJACK and self.game_process:
            try:
                info["game_name"] = self.game_process.name()
                info["game_pid"] = self.game_process.pid
            except Exception:
                pass
        
        return info
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.disconnect()

