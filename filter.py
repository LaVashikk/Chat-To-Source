import re
from settings import ConfigManager

class Filter:
    def __init__(self, config: ConfigManager) -> None:        
        bad_commands_regex = self._create_regex(config.GetBadCommand())
        bad_ents_regex = self._create_regex(config.GetBadEnts())
        
        self.filters = [
            CommandFilter(bad_commands_regex),
            EntityFilter(bad_ents_regex),
            CvarValueValidator(config)
        ]
        
        
    def _create_regex(_, info: list):
        part = '|'.join(info) # todo
        return re.compile(part, re.IGNORECASE)
    
    
    def filtrate(self, text: str):
        commands = text.split(";")
        filtered = []
        forbidden = []
        
        for command in commands:
            for test in self.filters:
                if test.IsBadCommand(command):
                    forbidden.append(command)
                    break
            else:
                filtered.append(command)
        
        return filtered, forbidden



class CommandFilter:
    def __init__(self, bad_commands_regex: list) -> None:
        self.bad_commands_regex = bad_commands_regex

    def IsBadCommand(self, command: str) -> bool:
        return self.bad_commands_regex.search(command)
    
    
class EntityFilter:
    def __init__(self, bad_ents_regex: list) -> None:
        self.bad_ents_regex = bad_ents_regex

    def IsBadCommand(self, command: str) -> bool:
        return self.bad_ents_regex.search(command)
    
    
class CvarValueValidator:
    def __init__(self, config: dict) -> None:
        self.config = config

    def IsBadCommand(self, command: str) -> bool:
        command_name = command.split()[0]
        individual_cvars = self.config.get("INDIVIDUAL_MAX_COMMAND_VALUE")
        cvar_value = self.config.get("MaxCvarValue")
        
        max_cvar_value = individual_cvars.get(command_name, cvar_value)
        
        for value in re.findall('\d+', command):
            if int(value) > max_cvar_value:
                return True
            
        return False