"""
Chat manager for handling YouTube and Twitch stream connections.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

try:
    import pytchat
except ImportError:
    pytchat = None

try:
    import twitchio
except ImportError:
    twitchio = None


@dataclass
class ChatAuthor:
    """Represents a chat message author."""
    name: str
    image_url: str = ""


@dataclass
class ChatMessage:
    """Represents a chat message."""
    author: ChatAuthor
    message: str
    timestamp: Optional[str] = None


class BaseChatClient(ABC):
    """Abstract base class for chat clients."""
    
    def __init__(self, stream_identifier: str):
        self.stream_identifier = stream_identifier
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the chat service."""
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the connection is still valid."""
        pass
    
    @abstractmethod
    def get_messages(self) -> List[ChatMessage]:
        """Get new messages from the chat."""
        pass
    
    def disconnect(self):
        """Disconnect from the chat service."""
        self._is_connected = False


class YouTubeChat(BaseChatClient):
    """YouTube chat client using pytchat."""
    
    def __init__(self, video_id: str):
        super().__init__(video_id)
        self.chat = None
        self.connect()
    
    def connect(self) -> bool:
        """Connect to YouTube chat."""
        if pytchat is None:
            self.logger.error("pytchat is not installed. Install it with: pip install pytchat")
            return False
        
        try:
            self.logger.info(f"Connecting to YouTube stream: {self.stream_identifier}")
            self.chat = pytchat.create(video_id=self.stream_identifier)
            self._is_connected = True
            self.logger.info("Successfully connected to YouTube chat")
            return True
        except pytchat.InvalidVideoIdException:
            self.logger.error(f"Invalid YouTube video ID: {self.stream_identifier}")
            self.chat = None
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to YouTube chat: {e}")
            self.chat = None
            return False
    
    def is_valid(self) -> bool:
        """Check if YouTube chat connection is valid."""
        if not self._is_connected or self.chat is None:
            return False
        return self.chat.is_alive()
    
    def get_messages(self) -> List[ChatMessage]:
        """Get new messages from YouTube chat."""
        if not self.is_valid():
            return []
        
        try:
            messages = []
            for item in self.chat.get().sync_items():
                author = ChatAuthor(
                    name=item.author.name,
                    image_url=getattr(item.author, 'imageUrl', '')
                )
                message = ChatMessage(
                    author=author,
                    message=item.message,
                    timestamp=getattr(item, 'timestamp', None)
                )
                messages.append(message)
            return messages
        except Exception as e:
            self.logger.error(f"Error getting YouTube messages: {e}")
            return []
    
    def disconnect(self):
        """Disconnect from YouTube chat."""
        super().disconnect()
        if self.chat:
            self.chat.terminate()
            self.chat = None


class TwitchChat(BaseChatClient):
    """Twitch chat client using twitchio."""
    
    def __init__(self, channel: str, token: Optional[str] = None):
        super().__init__(channel)
        self.token = token
        self.bot = None
        self._message_queue = []
        self.connect()
    
    def connect(self) -> bool:
        """Connect to Twitch chat."""
        if twitchio is None:
            self.logger.error("twitchio is not installed. Install it with: pip install twitchio")
            return False
        
        try:
            self.logger.info(f"Connecting to Twitch channel: {self.stream_identifier}")
            
            class TwitchBot(twitchio.Client):
                def __init__(self, token, channel, message_queue):
                    super().__init__(token=token)
                    self.channel = channel
                    self.message_queue = message_queue
                
                async def event_ready(self):
                    print(f'Logged in as | {self.nick}')
                    await self.join_channels([self.channel])
                
                async def event_message(self, message):
                    if message.echo:
                        return
                    
                    author = ChatAuthor(
                        name=message.author.name,
                        image_url=""  # Twitch doesn't provide avatar URLs easily
                    )
                    chat_message = ChatMessage(
                        author=author,
                        message=message.content,
                        timestamp=str(message.timestamp) if hasattr(message, 'timestamp') else None
                    )
                    self.message_queue.append(chat_message)
            
            self.bot = TwitchBot(self.token, self.stream_identifier, self._message_queue)
            self._is_connected = True
            self.logger.info("Successfully connected to Twitch chat")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Twitch chat: {e}")
            return False
    
    def is_valid(self) -> bool:
        """Check if Twitch chat connection is valid."""
        return self._is_connected and self.bot is not None
    
    def get_messages(self) -> List[ChatMessage]:
        """Get new messages from Twitch chat."""
        if not self.is_valid():
            return []
        
        messages = self._message_queue.copy()
        self._message_queue.clear()
        return messages
    
    def disconnect(self):
        """Disconnect from Twitch chat."""
        super().disconnect()
        if self.bot:
            # Note: twitchio doesn't have a simple disconnect method
            # In a real implementation, you'd need to handle the asyncio loop properly
            self.bot = None


def create_chat_client(platform: str, identifier: str, **kwargs) -> Optional[BaseChatClient]:
    """Factory function to create chat clients."""
    platform = platform.lower()
    
    if platform == 'youtube':
        return YouTubeChat(identifier)
    elif platform == 'twitch':
        token = kwargs.get('token')
        return TwitchChat(identifier, token)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

