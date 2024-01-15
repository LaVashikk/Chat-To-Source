import time 

import settings
import filter

from chat_manager import YTChat
from sourceBridge import SourceBridge


def init():
    config = settings.ConfigManager('config.json', 'forbidden_commands.json')
    commands_filter = filter.Filter(config)
    
    game = SourceBridge()
    if game.IsValid() is False:
        return exit("Could not connect to compatible Source Game.")
    
    chat = YTChat(config.get("StreamID"))
    if chat.IsValid() is False:
        return exit("Incorrect stream URL.")
    
    return config, commands_filter, game, chat



def main(): 
    config, commands_filter, game, chat = init()
    
    while chat.IsValid():
        for msg in chat.GetMessanges():
            message_text = msg.message
            commands = commands_filter.filtrate(message_text)
            for command in commands:
                game.run(command)  
            
        time.sleep(config.get("ChatInterval"))
    
    print("Stream offline now, goodbye!")


if __name__ == '__main__':
    main()