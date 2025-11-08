"""
Chat filter for filtering commands and messages.
"""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

from ..utils import ConfigManager


@dataclass
class FilterResult:
    """Result of filtering a message."""
    allowed_commands: List[str]
    forbidden_commands: List[str]
    filtered_message: str


class FilterBase(ABC):
    """Abstract base class for filters."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def is_bad_command(self, command: str) -> bool:
        """Check if a command should be filtered."""
        pass


class CommandFilter(FilterBase):
    """Filter for forbidden commands."""
    
    def __init__(self, config: ConfigManager):
        super().__init__(config)
        forbidden_commands = config.get_forbidden_commands()
        self.regex = self._create_regex(forbidden_commands)
    
    def _create_regex(self, commands: List[str]) -> re.Pattern:
        """Create regex pattern from command list."""
        if not commands:
            return re.compile(r'(?!.*)', re.IGNORECASE)  # Never matches
        
        escaped_commands = [re.escape(cmd) for cmd in commands]
        pattern = '|'.join(escaped_commands)
        return re.compile(pattern, re.IGNORECASE)
    
    def is_bad_command(self, command: str) -> bool:
        """Check if command is forbidden."""
        return bool(self.regex.search(command))


class EntityFilter(FilterBase):
    """Filter for forbidden entities."""
    
    def __init__(self, config: ConfigManager):
        super().__init__(config)
        forbidden_entities = config.get_forbidden_entities()
        self.regex = self._create_regex(forbidden_entities)
    
    def _create_regex(self, entities: List[str]) -> re.Pattern:
        """Create regex pattern from entity list."""
        if not entities:
            return re.compile(r'(?!.*)', re.IGNORECASE)  # Never matches
        
        escaped_entities = [re.escape(ent) for ent in entities]
        pattern = '|'.join(escaped_entities)
        return re.compile(pattern, re.IGNORECASE)
    
    def is_bad_command(self, command: str) -> bool:
        """Check if command contains forbidden entities."""
        return bool(self.regex.search(command))


class ScriptFilter(FilterBase):
    """Filter for script commands with exceptions."""
    
    def __init__(self, config: ConfigManager):
        super().__init__(config)
        bad_scripts = config.get_forbidden_scripts()
        good_scripts = config.get_script_exceptions()
        
        self.bad_scripts_regex = self._create_regex(bad_scripts)
        self.good_scripts_regex = self._create_regex(good_scripts)
    
    def _create_regex(self, scripts: List[str]) -> re.Pattern:
        """Create regex pattern from script list."""
        if not scripts:
            return re.compile(r'(?!.*)', re.IGNORECASE)  # Never matches
        
        escaped_scripts = [re.escape(script) for script in scripts]
        pattern = '|'.join(escaped_scripts)
        return re.compile(pattern, re.IGNORECASE)
    
    def is_bad_command(self, command: str) -> bool:
        """Check if command is a bad script but not in exceptions."""
        has_bad_script = bool(self.bad_scripts_regex.search(command))
        has_good_script = bool(self.good_scripts_regex.search(command))
        return has_bad_script and not has_good_script


class CvarValueFilter(FilterBase):
    """Filter for cvar values that exceed limits."""
    
    def __init__(self, config: ConfigManager):
        super().__init__(config)
        self.cvar_limits = config.get_cvar_limits()
        self.enabled = self.cvar_limits.get('enable_filter', True)
        self.default_max = self.cvar_limits.get('default_max', 100)
        self.individual_max = self.cvar_limits.get('individual_max', {})
    
    def is_bad_command(self, command: str) -> bool:
        """Check if command has cvar values exceeding limits."""
        if not self.enabled:
            return False
        
        command_parts = command.split()
        if not command_parts:
            return False
        
        command_name = command_parts[0]
        max_value = self.individual_max.get(command_name, self.default_max)
        
        # Find all numeric values in the command
        numeric_values = re.findall(r'\d+', command)
        
        try:
            return any(int(value) > max_value for value in numeric_values)
        except ValueError:
            return False


class ChatFilter:
    """Main chat filter that combines all filter types."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize all filters
        self.filters = [
            CommandFilter(config),
            EntityFilter(config),
            ScriptFilter(config),
            CvarValueFilter(config)
        ]
        
        # Command extraction pattern
        self.command_pattern = re.compile(r'[!+](\w+(?:\s+[^\s!+]+)*)', re.IGNORECASE)
    
    def extract_commands(self, message: str) -> List[str]:
        """Extract commands from a chat message."""
        commands = []
        matches = self.command_pattern.findall(message)
        
        for match in matches:
            # Clean up the command
            command = match.strip()
            if command:
                commands.append(command)
        
        return commands
    
    def filter_commands(self, commands: List[str]) -> Tuple[List[str], List[str]]:
        """Filter commands into allowed and forbidden lists."""
        allowed = []
        forbidden = []
        
        for command in commands:
            is_forbidden = False
            
            # Check against all filters
            for filter_instance in self.filters:
                if filter_instance.is_bad_command(command):
                    is_forbidden = True
                    break
            
            if is_forbidden:
                forbidden.append(command)
            else:
                allowed.append(command)
        
        return allowed, forbidden
    
    def filter_message(self, message: str) -> FilterResult:
        """Filter a complete message and return results."""
        # Extract commands from message
        commands = self.extract_commands(message)
        
        # Filter commands
        allowed, forbidden = self.filter_commands(commands)
        
        # Create filtered message with forbidden commands highlighted
        filtered_message = message
        for forbidden_cmd in forbidden:
            # Highlight forbidden commands in red
            pattern = re.compile(re.escape(forbidden_cmd), re.IGNORECASE)
            filtered_message = pattern.sub(f"[red]{forbidden_cmd}[/red]", filtered_message)
        
        return FilterResult(
            allowed_commands=allowed,
            forbidden_commands=forbidden,
            filtered_message=filtered_message
        )
    
    def is_message_allowed(self, message: str) -> bool:
        """Quick check if a message contains any forbidden content."""
        commands = self.extract_commands(message)
        _, forbidden = self.filter_commands(commands)
        return len(forbidden) == 0

