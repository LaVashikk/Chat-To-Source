import time
import pytchat
import re
import json
import subprocess

config = json.load(open('config.json'))
all_command_config = json.load(open('forbidden_commands.json'))

forbidden_commands = []
for key in all_command_config:
    if config[f"ENABLE_{key}_COMMAND"]:
        forbidden_commands += all_command_config[key]
        
forbidden_re = re.compile('|'.join(forbidden_commands), re.IGNORECASE)

blocked_command = []

""" TODO 
? Добавить логирование в файл, для дальнейшего разбора при необходимости
    + Ответ про запрещенку в чате от бота
* Улучшить фильтр
    + Отсортировать запрещенку 
    + Блокировку ent команд
* Добавить поддержку DonationAlert (необязательно)
* Разбить код на необходимые составляющие (необязательно)
"""


# Запускает игру с аргументами
def run_game_with_commands(commands: list[str]) -> None:
    args = [config['EXE_FILE_PATH'], "-hijack"]
    for command in commands:
        args.append(f"+{command}")

    print(*commands,sep="\n") #DEVCODE
    if blocked_command:
        args.append(f"+say Blocked commands: {', '.join(blocked_command)}")
        blocked_command.clear()
    print(f"ARG: {args}")
    subprocess.run(args)
    

# Фильтрация команд
def filter_commands(commands: list[str]) -> list[str]:
    # global blocked_command
    filtered = []
    for command in commands:
        if forbidden_re.search(command):
            blocked_command.append(command)
            continue
        if command.startswith('ent_') and any(re.search(fr"\b{entity}\b", command) for entity in config['CORRUPTED_ENTITY']): #TODO bruh
            blocked_command.append(command)
            continue
        value = re.findall('\d+', command)
        max_command_value = config['INDIVIDUAL_MAX_COMMAND_VALUE'].get(command.split()[0], config['MAX_COMMAND_VALUE'])
        if not value or int(value[0]) <= max_command_value:
            filtered.append(command)
    return filtered


        
# Разделение и проверка команд в сообщении
def process_message(message: str) -> list[str]:
    commands = message.split(';')
    commands = [command.strip() for command in commands]
    
    allowed_commands = filter_commands(commands)
    return allowed_commands


def main() -> None:
    live_chat = pytchat.create(config['STREAM_ID'])
    try:
        while live_chat.is_alive():
            chat_messages = live_chat.get().sync_items()
            all_commands = []

            for chat in chat_messages:
                message = chat.message #.lower()
                # выводим информацию о сообщении в консоль (для отладки)
                print(f"{chat.datetime} [{chat.author.name}] - {message}")
                allowed_commands = process_message(message)
                all_commands += allowed_commands # list + list
            
            if all_commands:
                run_game_with_commands(all_commands)
            print(1)

            time.sleep(config['CHAT_INTERVAL'])
            
        print("Steam оффлайн")
    except Exception as e:
        # если произошла какая-то ошибка, выводим ее в консоль
        print(f"Произошла ошибка: {e}")


if __name__ == '__main__':
    main()