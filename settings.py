import json

class ConfigManager:
    def get(self, idx, default_value = None):
        return self.config.get(idx, default_value)


    def __init__(self, config_path: str, command_config_path: str):
        self.config = self._read_config(config_path)
        self.forbidden_config = self._read_config(command_config_path)
        
        self.forbidden_commands = self._get_forbidden_elements("Commands")
        self.forbidden_ents = self._get_forbidden_elements("Entities")

    def _read_config(self, path: str):
        with open(path, 'r') as file:
            return json.load(file)


    def _get_forbidden_elements(self, table: str):
        forbidden = []
        
        for key in self.forbidden_config[table]:
            if self.config["commandFilters"][key]:
                commands = self.forbidden_config[table][key]
                forbidden.extend(commands)
                
        return forbidden

    
    def GetBadCommand(self):
        return self.forbidden_commands
    
    
    def GetBadEnts(self):
        return self.forbidden_ents
    
    
    def GetBadScripts(self):
        return self.forbidden_config["Scripts"]["Corrupted"]
    
    def GetScriptsExceptions(self):
        return self.forbidden_config["Scripts"]["Allowed"]
    
    
    def _getitem_(self, idx):
        return self.get(idx)