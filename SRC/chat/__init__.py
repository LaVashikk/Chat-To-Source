from typing import Generator
from httpx import ReadTimeout, ConnectTimeout
import pytchat
from abc import ABC, abstractmethod
from pytchat.processors.default.processor import Chat as YtMsg

from .chat_filter import FilterBase, CommandFilter, EntityFilter, ScriptFilter, CvarValueValidator 

class Chat(ABC):
    filters: list[FilterBase] = [
        CommandFilter, EntityFilter, ScriptFilter, CvarValueValidator 
    ]
    
    @abstractmethod
    def is_valid(self) -> bool:
        pass
    
    @abstractmethod
    def get_messages(self) -> Generator:
        pass


class YouTube(Chat):
    def __init__(self, stream_link, try_count = 5) -> None:
        while try_count > 0:
            try:
                self.chat = pytchat.create(video_id=stream_link)
                print(self.chat.get())
                break
            except ReadTimeout or ConnectTimeout:
                print("try again...")
                try_count -= 1
        # pytchat.InvalidVideoIdException

    def is_valid(self) -> bool:
        if(self.chat is None):
            return False
        return self.chat.is_alive()

    def get_messages(self) -> Generator:
        return self.chat.get().sync_items()
    
    def get_messages_fileted(self) -> tuple[list[YtMsg], list[YtMsg]]:
        messages = []
        while len(messages) == 0:
            messages = list(self.get_messages())

        allow, forbidden = [], []
        for msg in messages:
            (forbidden if self._is_bad(msg.message) else allow).append(msg)

        return allow, forbidden

    
    def _is_bad(self, text: str) -> bool:
        return any(filter.is_bad_command(text) for filter in self.filters)