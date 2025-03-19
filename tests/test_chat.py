import conftest
from SRC import chat

URL = "-5R-aLmZ9Ps"

chat_handler = chat.YouTube(URL)
print("Connected!")

while chat_handler.is_valid():
    allow, forbidden = chat_handler.get_messages_fileted()
    for msg in allow:
        print(f"allow: {msg.message}")
    for msg in forbidden:
        print(f"forb: {msg.message}")