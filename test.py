import json

config = json.load(open('config.json'))
all_command_config = json.load(open('forbidden_commands.json'))
forbidden_commands = []

for key in ['GAME_BREAKERS', 'CHAOS_CREATORS', 'PLAYFUNCTION_KILLERS', 'GAMEPLAY_HINDERERS', 'IRRITATION_INVOKERS']:
    if config[f"ENABLE_{key}_COMMAND"]:
        forbidden_commands += all_command_config[key]
        
print(forbidden_commands)


print(forbidden_commands)