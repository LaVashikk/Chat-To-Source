import time
import pytchat
from server import run_server

stream_id = "xGASqm8qu50"  # Замени сюда свой ID стрима
live_chat = pytchat.create(stream_id)
print(live_chat.is_alive())

def messages_generator():
    chat_data = live_chat.get().sync_items()

    for chat_item in chat_data:
        print(chat_item.message)  # для проверки, что сообщения приходят
        yield f"data: {chat_item.message},10\n\n"

if __name__ == "__main__":
    run_server(messages_generator)