import re
from settings import ConfigManager

class Filter:
    def __init__(self, config: ConfigManager) -> None:        
        bad_commands_regex = self._create_regex(config.GetBadCommand())
        bad_ents_regex = self._create_regex(config.GetBadEnts())
        
        bad_scripts_regex = self._create_regex(config.GetBadScripts())
        good_script_regex = self._create_regex(config.GetScriptsExceptions())
        
        self.filters = [
            CommandFilter(bad_commands_regex),
            EntityFilter(bad_ents_regex),
            ScriptFilter(bad_scripts_regex, good_script_regex),
            CvarValueValidator(config)
        ]
        
        
    def _create_regex(_, info: list):
        escaped_info = [re.escape(i) for i in info]
        part = '|'.join(escaped_info) # todo
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
    def __init__(self, bad_commands_regex: re.compile) -> None:
        self.bad_commands_regex = bad_commands_regex

    def IsBadCommand(self, command: str) -> bool:
        return self.bad_commands_regex.search(command) # and not self.good_commands_regex.search(command)
     
    
class EntityFilter:
    def __init__(self, bad_ents_regex: re.compile) -> None:
        self.bad_ents_regex = bad_ents_regex

    def IsBadCommand(self, command: str) -> bool:
        return self.bad_ents_regex.search(command)
    
    
class ScriptFilter:
    def __init__(self, bad_scripts_regex: re.compile, good_script_regex: re.compile) -> None:
        self.bad_scripts_regex = bad_scripts_regex
        self.good_script_regex = good_script_regex

    def IsBadCommand(self, command: str) -> bool:
        return self.bad_scripts_regex.search(command) and not self.good_script_regex.search(command)
    
    
class CvarValueValidator:
    def __init__(self, config: dict) -> None:
        self.config = config

    def IsBadCommand(self, command: str) -> bool:
        cvar_info = self.config.config["cvarLimits"]
        command_name = command.split()
        
        if len(command_name) < 0 or not cvar_info["enableFilter"]:
            return False
        
        cvar_value = cvar_info["defaultMax"]
        max_cvar_value = cvar_info["individualMax"].get(command_name[0], cvar_value)
        
        for value in re.findall('\d+', command):
            if int(value) > max_cvar_value:
                return True
            
        return False