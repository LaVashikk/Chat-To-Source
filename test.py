import time
import pytchat
import re
import json
import subprocess
from typing import List
import datetime
import keyboard    # You need to install this module: pip install keyboard
import os


# ... (previous functions are the same)

def run_game_with_commands(commands: List[str], blocked_command: List[str]) -> None:
    args = [config['EXE_FILE_PATH'], "-hijack", *[f"+{command}" for command in commands]]
    if blocked_command:
        args.append(f"+say Blocked commands: {', '.join(blocked_command)}")
        blocked_command.clear()

    print("\n".join(commands))
    print(f"ARG: {args}")
    process = subprocess.Popen(args)    # Change this line from `subprocess.run`
    process.communicate()


def write_log(chat_messages: list) -> None:
    log_filename = os.path.join(config["LOGS_DIR"], f"{datetime.date.today()}-chatlog.txt")

    with open(log_filename, "a", encoding="utf-8") as log_file:
        for chat in chat_messages:
            log_file.write(f"{chat.datetime} [{chat.author.name}] - {chat.message}\n"
                           f"   ALLOWED: {', '.join(filter_commands(chat.message.split(';')))}\n"
                           f"   BLOCKED: {', '.join(blocked_command)}\n")

# ... (main function is the same until the while loop)

while live_chat.is_alive():
    chat_messages = live_chat.get().sync_items()
    all_commands = []

    for chat in chat_messages:
        message = chat.message
        print(f"{chat.datetime} [{chat.author.name}] - {message}")
        allowed_commands = process_message(message)
        all_commands.extend(allowed_commands)

    if all_commands:
        run_game_with_commands(all_commands, blocked_command)
        write_log(chat_messages)
        all_commands.clear()

    if keyboard.is_pressed("r"):    # Change 'r' to any key you want to use to restart
        print("Restarting...")
        os.execv(sys.executable, ["python"] + sys.argv)

    time.sleep(config["CHAT_INTERVAL"])