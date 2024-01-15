import json

class ConfigManager:
    def get(self, idx, default_value = None):
        return self._config.get(idx, default_value)


    def __init__(self, config_path: str, command_config_path: str):
        self._config = self.__read_config(config_path)
        self._forbidden_commands_config = self.__read_config(command_config_path)
        
        self._forbidden_commands = self.__get_forbidden_commands()
        self._forbidden_ents = self.__get_forbidden_ents()

    def __read_config(self, path: str):
        with open(path, 'r') as file:
            return json.load(file)


    def __get_forbidden_commands(self):
        forbidden_commands = []
        
        for key in self._forbidden_commands_config:
            if self._config[f"ENABLE_{key}_COMMAND"] is True:
                commands = self._forbidden_commands_config[key]
                forbidden_commands.extend(commands)
                
        return forbidden_commands
    
    
    def __get_forbidden_ents(self):
        return self._config.get("CORRUPTED_ENTITY", "")
    
    
    def GetBadCommand(self):
        return self._forbidden_commands
    
    
    def GetBadEnts(self):
        return self._forbidden_ents
    
    
    def __getitem__(self, idx):
        return self.get(idx)