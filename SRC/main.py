# import argparse
# from typing import final

# parser = argparse.ArgumentParser(description='Описание вашей программы.')
# parser.add_argument('имя_файла', help='Имя файла для обработки')
# parser.add_argument('-v', '--verbose', action='store_true', help='Увеличить детализацию вывода')
# parser.add_argument('-o', '--output', help='Имя выходного файла')

# args = parser.parse_args()

# print(f"Имя файла: {args.имя_файла}")
# if args.verbose:
#     print("Детализация включена")
# if args.output:
#     print(f"Выходной файл: {args.output}")
    
    
# STREAM URL
# UPDATE TIME

# WIDGET PORT


# import time 

# import filter
# import utils

# from SRC.chat.chat_manager import YTChat
# from sourceBridge import SourceBridge
# from Widget.ChatWidget import ChatWidget

# def init():
#     config = utils.ConfigManager('config.json', 'forbidden_commands.json')
#     commands_filter = filter.Filter(config)
    
#     game = SourceBridge()
#     if game.is_valid() is False:
#         return exit("Could not connect to compatible Source Game.")
    
#     chat = YTChat(config.get("streamURL")) # change it as launch arg
#     if chat.IsValid() is False:
#         return exit("Incorrect stream URL.")
        
#     return config, commands_filter, game, chat



# def main(): 
#     config, commands_filter, game, chat = init()
#     widget.send_server("Reconnected...")
    
#     while chat.IsValid() and game.is_valid():
#         allowed_commands = []
#         forbidden_commands = []
#         for msg in chat.GetMessanges():
#             message_text = msg.message
#             allowed, forbidden = commands_filter.filtrate(message_text)
#             allowed_commands.extend(allowed)
#             forbidden_commands.extend(forbidden)
            
#             for i in forbidden:
#                 message_text = message_text.replace(i, f"[red]{i}[/red]")
#             widget.send_message(msg.author.imageUrl, msg.author.name, message_text)
        
#         if len(allowed_commands) > 0:
#             game.exec(allowed_commands) 
        
#         time.sleep(config.get("chatUpdateInterval")) # change it as launch arg
    
#     widget.send_server("Offline now!")
#     time.sleep(0.5)
#     print("Stream offline now, goodbye!")

import time

import utils
import chat
import game
import widget

class Chat2Source:
    # USE SLOTS!
    config: utils.ConfigManager = None
    _chat: chat.Chat = None
    _game: game = None
    _widget = None
    delay = 0
    
    def set_stream(self, url: str):
        print("Trying to connect to stream...")
        self._chat = chat.YouTube(url) # todo
    
    def start_pooling(self):
        while self.chat.is_valid() and self.game.is_valid():
            allowed, forbidden = [], []
            for msg in self.chat.get_messages():
                a, f = filter.filtrate(msg.message)
                allowed.extend(a)
                forbidden.extend(f)
                # widget logic!
            
            if len(allowed) > 0:
                self.game.exec(allowed)
            time.sleep(self.delay)
        