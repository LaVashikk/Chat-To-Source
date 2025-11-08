"""
Web-based chat widget for displaying chat messages and server status.
"""

import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS


class ChatWidget:
    """Web-based chat widget using Flask and SocketIO."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Flask app setup
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.app.config['SECRET_KEY'] = 'chat2source_secret_key'
        
        # Enable CORS for all routes
        CORS(self.app, cors_allowed_origins="*")
        
        # SocketIO setup
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Message storage
        self.messages: List[Dict] = []
        self.max_messages = 100
        self.server_status = "Disconnected"
        
        # Setup routes and events
        self._setup_routes()
        self._setup_socketio_events()
        
        # Server thread
        self._server_thread: Optional[threading.Thread] = None
        self._running = False
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main chat widget page."""
            return render_template('index.html')
        
        @self.app.route('/api/messages')
        def get_messages():
            """API endpoint to get recent messages."""
            return json.dumps({
                'messages': self.messages[-50:],  # Last 50 messages
                'status': self.server_status
            })
        
        @self.app.route('/api/status')
        def get_status():
            """API endpoint to get server status."""
            return json.dumps({
                'status': self.server_status,
                'message_count': len(self.messages)
            })
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            self.logger.info(f"Client connected: {request.sid}")
            # Send recent messages to newly connected client
            emit('message_history', {
                'messages': self.messages[-20:],  # Last 20 messages
                'status': self.server_status
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            self.logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_messages')
        def handle_request_messages():
            """Handle request for message history."""
            emit('message_history', {
                'messages': self.messages[-50:],
                'status': self.server_status
            })
    
    def start_server(self, threaded: bool = True) -> bool:
        """Start the web server."""
        if self._running:
            self.logger.warning("Server is already running")
            return False
        
        try:
            if threaded:
                self._server_thread = threading.Thread(
                    target=self._run_server,
                    daemon=True
                )
                self._server_thread.start()
                self.logger.info(f"Chat widget server starting on {self.host}:{self.port}")
            else:
                self._run_server()
            
            self._running = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False,
                log_output=not self.debug
            )
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self._running = False
    
    def stop_server(self):
        """Stop the web server."""
        self._running = False
        if self._server_thread and self._server_thread.is_alive():
            self.logger.info("Stopping chat widget server")
            # Note: SocketIO doesn't have a clean shutdown method
            # In production, you might want to use a more sophisticated approach
    
    def send_message(self, author_image: str, author_name: str, message: str, timestamp: Optional[str] = None):
        """Send a chat message to all connected clients."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        message_data = {
            'type': 'chat',
            'author_image': author_image,
            'author_name': author_name,
            'message': message,
            'timestamp': timestamp
        }
        
        # Add to message history
        self.messages.append(message_data)
        
        # Limit message history
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Broadcast to all connected clients
        self.socketio.emit('new_message', message_data)
        
        self.logger.debug(f"Sent message from {author_name}: {message}")
    
    def send_server_message(self, message: str, message_type: str = "info"):
        """Send a server status message to all connected clients."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message_data = {
            'type': 'server',
            'message': message,
            'message_type': message_type,  # info, warning, error, success
            'timestamp': timestamp
        }
        
        # Add to message history
        self.messages.append(message_data)
        
        # Limit message history
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Broadcast to all connected clients
        self.socketio.emit('server_message', message_data)
        
        self.logger.info(f"Sent server message: {message}")
    
    def update_status(self, status: str):
        """Update server status and notify clients."""
        self.server_status = status
        self.socketio.emit('status_update', {'status': status})
        self.logger.info(f"Status updated: {status}")
    
    def clear_messages(self):
        """Clear all message history."""
        self.messages.clear()
        self.socketio.emit('messages_cleared')
        self.logger.info("Message history cleared")
    
    def get_url(self) -> str:
        """Get the widget URL."""
        return f"http://{self.host}:{self.port}"
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running
    
    def get_stats(self) -> Dict:
        """Get widget statistics."""
        return {
            'running': self._running,
            'message_count': len(self.messages),
            'status': self.server_status,
            'url': self.get_url()
        }

