import pytchat

class YTChat:
    def __init__(self, stream_link) -> None:
        try:
            print("Trying to connect to stream...")
            self.chat = pytchat.create(video_id=stream_link)
            print("Connected to stream!")
        except pytchat.InvalidVideoIdException:
            self.chat = None

    def IsValid(self):
        if(self.chat is None):
            return False
        return self.chat.is_alive()

    def GetMessanges(self):
        return self.chat.get().sync_items()

