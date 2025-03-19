import re
from SRC.utils import ConfigManager
from dataclasses import dataclass
from abc import ABC, abstractmethod

def _create_regex(info: list) -> re.Pattern:
        escaped_info = [re.escape(i) for i in info]
        part = '|'.join(escaped_info)
        return re.compile(part, re.IGNORECASE)

config = ConfigManager('settings.toml', 'forbidden_config.toml')
    
class FilterBase(ABC):
    @classmethod
    def is_bad_command(cls, command: str) -> bool:
        return bool(cls.regex.search(command))

    
class CommandFilter(FilterBase):
    regex = _create_regex(config.GetBadCommand())


class EntityFilter(FilterBase):
    regex = _create_regex(config.GetBadEnts())


class ScriptFilter(FilterBase):
    bad_scripts_regex = _create_regex(config.GetBadScripts())
    good_script_regex = _create_regex(config.GetScriptsExceptions())

    @classmethod
    def is_bad_command(cls, command: str) -> bool:
        return bool(cls.bad_scripts_regex.search(command)) and not cls.good_script_regex.search(command)


# TODO bruh
class CvarValueValidator(FilterBase):
    cvar_info = config.config["cvarLimits"]
    enabled = cvar_info["enableFilter"]
    cvar_max = cvar_info["defaultMax"]

    @classmethod
    def is_bad_command(cls, command: str) -> bool:
        if not cls.enabled:
            return False

        command_parts = command.split()
        if not command_parts:
            return False

        command_name = command_parts[0]
        max_cvar_value = cls.cvar_info["individualMax"].get(command_name, cls.cvar_max)

        return any(int(value) > max_cvar_value for value in re.findall(r'\d+', command))
