import time 

import settings
import filter

from chat_manager import YTChat
from sourceBridge import SourceBridge
from Widget.ChatWidget import ChatWidget

def init():
    config = settings.ConfigManager('config.json', 'forbidden_commands.json')
    commands_filter = filter.Filter(config)
    
    game = SourceBridge()
    if game.is_valid() is False:
        return exit("Could not connect to compatible Source Game.")
    
    chat = YTChat(config.get("streamURL"))
    if chat.IsValid() is False:
        return exit("Incorrect stream URL.")
    
    widget = ChatWidget("127.0.0.1", 5000)
    
    return config, commands_filter, game, chat, widget



def main(): 
    config, commands_filter, game, chat, widget = init()
    widget.send_server("Reconnected...")
    
    while chat.IsValid() and game.is_valid():
        allowed_commands = []
        forbidden_commands = []
        for msg in chat.GetMessanges():
            message_text = msg.message
            allowed, forbidden = commands_filter.filtrate(message_text) # todo
            allowed_commands.extend(allowed)
            forbidden_commands.extend(forbidden)
            
            for i in forbidden:
                message_text = message_text.replace(i, f"[red]{i}[/red]")
            widget.send_message(msg.author.imageUrl, msg.author.name, message_text)
        
        if len(allowed_commands) > 0:
            game.run(allowed_commands) 
        
        time.sleep(config.get("chatUpdateInterval"))
    
    widget.send_server("Offline now!")
    time.sleep(0.5)
    print("Stream offline now, goodbye!")


if __name__ == '__main__':
    main()