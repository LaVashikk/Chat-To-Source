import time 

import settings
import filter

from chat_manager import YTChat
from sourceBridge import SourceBridge


def init():
    config = settings.ConfigManager('config.json', 'forbidden_commands.json')
    commands_filter = filter.Filter(config)
    
    game = SourceBridge()
    if game.is_valid() is False:
        return exit("Could not connect to compatible Source Game.")
    
    chat = YTChat(config.get("StreamID"))
    if chat.IsValid() is False:
        return exit("Incorrect stream URL.")
    
    return config, commands_filter, game, chat



def main(): 
    config, commands_filter, game, chat = init()
    
    while chat.IsValid() and game.is_valid():
        # allowed_commands = []
        forbidden_commands = []
        for msg in chat.GetMessanges():
            message_text = msg.message
            commands, forbidden = commands_filter.filtrate(message_text) # todo
            print(f"DEV: {commands}")
            game.run(commands) 
            forbidden_commands.extend(forbidden)   #* dev code?
        
        if len(forbidden_commands) > 0:
            game.run(f"say bad command: {', '.join(forbidden_commands)}")  #* dev code
            
        time.sleep(config.get("ChatInterval"))
    
    print("Stream offline now, goodbye!")


if __name__ == '__main__':
    main()