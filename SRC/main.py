"""
Chat2Source - Main application entry point.
Connects YouTube/Twitch chat to Source Engine games.
"""

import argparse
import logging
import signal
import sys
import time
from typing import Optional

from .utils import ConfigManager, setup_logging, validate_stream_url, extract_stream_identifier
from .chat import create_chat_client, ChatFilter
from .game import SourceBridge
from .widget import ChatWidget


class Chat2Source:
    """Main application class for Chat2Source."""
    
    def __init__(self, config_file: str = "settings.toml", forbidden_file: str = "forbidden_config.toml"):
        # Load configuration
        self.config = ConfigManager(config_file, forbidden_file)
        
        # Setup logging
        setup_logging(self.config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.chat_client = None
        self.game_bridge = None
        self.widget = None
        self.chat_filter = None
        
        # Application state
        self.running = False
        self.update_interval = self.config.get("stream.update_interval", 1.0)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize(self, stream_url: Optional[str] = None, platform: Optional[str] = None) -> bool:
        """Initialize all components."""
        self.logger.info("Initializing Chat2Source...")
        
        # Use provided parameters or config values
        if stream_url is None:
            stream_url = self.config.get("stream.url")
        if platform is None:
            platform = self.config.get("stream.platform", "youtube")
        
        # Validate stream URL
        if not validate_stream_url(stream_url, platform):
            self.logger.error(f"Invalid stream URL: {stream_url} for platform: {platform}")
            return False
        
        # Extract stream identifier
        stream_identifier = extract_stream_identifier(stream_url, platform)
        if not stream_identifier:
            self.logger.error(f"Could not extract stream identifier from: {stream_url}")
            return False
        
        # Initialize chat filter
        self.chat_filter = ChatFilter(self.config)
        
        # Initialize game bridge
        netcon_host = self.config.get("game.netcon_host", "127.0.0.1")
        netcon_port = self.config.get("game.netcon_port", 2121)
        self.game_bridge = SourceBridge(netcon_host, netcon_port)
        
        if not self.game_bridge.is_valid():
            self.logger.error("Could not connect to Source Engine game")
            return False
        
        # Initialize chat client
        self.chat_client = create_chat_client(platform, stream_identifier)
        if not self.chat_client or not self.chat_client.is_valid():
            self.logger.error(f"Could not connect to {platform} chat")
            return False
        
        # Initialize widget
        widget_host = self.config.get("widget.host", "127.0.0.1")
        widget_port = self.config.get("widget.port", 5000)
        widget_debug = self.config.get("widget.debug", False)
        
        self.widget = ChatWidget(widget_host, widget_port, widget_debug)
        if not self.widget.start_server(threaded=True):
            self.logger.error("Could not start chat widget server")
            return False
        
        self.logger.info("Chat2Source initialized successfully")
        self.logger.info(f"Chat widget available at: {self.widget.get_url()}")
        self.logger.info(f"Game connection: {self.game_bridge.get_connection_info()}")
        
        return True
    
    def start(self) -> bool:
        """Start the main application loop."""
        if not self.chat_client or not self.game_bridge or not self.widget:
            self.logger.error("Components not initialized. Call initialize() first.")
            return False
        
        self.running = True
        self.logger.info("Starting Chat2Source main loop...")
        
        # Send initial status message
        self.widget.send_server_message("Chat2Source connected and ready!", "success")
        self.widget.update_status("Connected")
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            return False
        finally:
            self.stop()
        
        return True
    
    def _main_loop(self):
        """Main application loop."""
        while self.running:
            try:
                # Check if connections are still valid
                if not self._check_connections():
                    if self.config.get("game.auto_reconnect", True):
                        self._attempt_reconnection()
                    else:
                        break
                
                # Process chat messages
                self._process_chat_messages()
                
                # Sleep for update interval
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in main loop iteration: {e}")
                time.sleep(1)  # Brief pause before retrying
    
    def _check_connections(self) -> bool:
        """Check if all connections are valid."""
        chat_valid = self.chat_client and self.chat_client.is_valid()
        game_valid = self.game_bridge and self.game_bridge.is_valid()
        
        if not chat_valid:
            self.logger.warning("Chat connection lost")
            self.widget.send_server_message("Chat connection lost", "warning")
        
        if not game_valid:
            self.logger.warning("Game connection lost")
            self.widget.send_server_message("Game connection lost", "warning")
        
        return chat_valid and game_valid
    
    def _attempt_reconnection(self):
        """Attempt to reconnect to lost connections."""
        self.logger.info("Attempting to reconnect...")
        self.widget.send_server_message("Attempting to reconnect...", "info")
        
        # Try to reconnect to game
        if not self.game_bridge.is_valid():
            if self.game_bridge.connect():
                self.logger.info("Game reconnection successful")
                self.widget.send_server_message("Game reconnected", "success")
            else:
                self.logger.error("Game reconnection failed")
                self.widget.send_server_message("Game reconnection failed", "error")
        
        # Chat client reconnection would need to be implemented per platform
        # For now, we'll just log the issue
        if not self.chat_client.is_valid():
            self.logger.error("Chat reconnection not implemented")
            self.widget.send_server_message("Chat reconnection failed", "error")
    
    def _process_chat_messages(self):
        """Process new chat messages."""
        try:
            messages = self.chat_client.get_messages()
            
            for message in messages:
                # Filter the message
                filter_result = self.chat_filter.filter_message(message.message)
                
                # Send message to widget
                self.widget.send_message(
                    message.author.image_url,
                    message.author.name,
                    filter_result.filtered_message,
                    message.timestamp
                )
                
                # Execute allowed commands
                if filter_result.allowed_commands:
                    self.logger.info(f"Executing {len(filter_result.allowed_commands)} commands")
                    success = self.game_bridge.execute_commands(filter_result.allowed_commands)
                    
                    if not success:
                        self.logger.warning("Failed to execute some commands")
                
                # Log forbidden commands
                if filter_result.forbidden_commands:
                    self.logger.info(f"Blocked {len(filter_result.forbidden_commands)} forbidden commands")
        
        except Exception as e:
            self.logger.error(f"Error processing chat messages: {e}")
    
    def stop(self):
        """Stop the application."""
        if not self.running:
            return
        
        self.logger.info("Stopping Chat2Source...")
        self.running = False
        
        # Send shutdown message
        if self.widget:
            self.widget.send_server_message("Chat2Source shutting down", "info")
            self.widget.update_status("Offline")
        
        # Cleanup components
        if self.chat_client:
            self.chat_client.disconnect()
        
        if self.game_bridge:
            self.game_bridge.disconnect()
        
        if self.widget:
            self.widget.stop_server()
        
        self.logger.info("Chat2Source stopped")
    
    def get_status(self) -> dict:
        """Get application status."""
        return {
            "running": self.running,
            "chat_connected": self.chat_client and self.chat_client.is_valid(),
            "game_connected": self.game_bridge and self.game_bridge.is_valid(),
            "widget_running": self.widget and self.widget.is_running(),
            "widget_url": self.widget.get_url() if self.widget else None
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Chat2Source - Connect stream chat to Source Engine games")
    parser.add_argument("--stream-url", "-u", help="Stream URL or identifier")
    parser.add_argument("--platform", "-p", choices=["youtube", "twitch"], help="Streaming platform")
    parser.add_argument("--config", "-c", default="settings.toml", help="Configuration file")
    parser.add_argument("--forbidden", "-f", default="forbidden_config.toml", help="Forbidden commands file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Create and initialize application
    app = Chat2Source(args.config, args.forbidden)
    
    # Override logging level if verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize with command line arguments
    if not app.initialize(args.stream_url, args.platform):
        print("Failed to initialize Chat2Source")
        sys.exit(1)
    
    # Start the application
    if not app.start():
        print("Failed to start Chat2Source")
        sys.exit(1)


if __name__ == "__main__":
    main()

