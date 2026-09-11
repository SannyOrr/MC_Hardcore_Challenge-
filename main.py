"""
Minecraft hardcore controller

A simple script that can help me stick to the rules of Minecraft,
tracking my hardcore stats and automaticlly deleting worlds
"""

# IMPORTS
import os
import re
import subprocess
import sys
import json
import shutil
from pathlib import Path
import time

# CONFIG

SERVER_DIR = Path("server")
WORLD_DIR = SERVER_DIR / "world"
STATS_FILE = Path("stats.json")

JAVA_COMMAND = [
    "java",
    "-Xmx4G",
    "-Xms2G",
    "-jar",
    "server.jar",
    "nogui"
]

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

death_messages = [
    "died",
    "drowned",
    "death",
    "experienced kinetic energy",
    "intentional game design",
    "blew up",
    "pummeled",
    "blown up",
    "killed",
    "hit the ground too hard",
    "fell",
    "left the confines of this world",
    "squished",
    "suffocated",
    "was burnt",
    "cactus",
    "was slain",
    "was shot",
    "burned to death",
    "tried to swim in lava",
    "got melted by a blaze",
    "failed to escape the Nether",
    "fell out of the world",
    "withered away",
    "discovered the void",
    "discovered the floor was lava",
    "was doomed by the Wither",
    "got struck by lightning",
    "got caught in a trap",
    "was pricked to death",
    "got stung by a bee",
    "was stung to death",
    "stung",
    "doomed to fall",
    "starved to death",
    "was doomed by a witch",
    "fell into a ravine",
    "was fireballed",
    "was shot by a Skeleton",
    "was blown off a cliff",
    "got suffocated in a wall",
    "was slain by a zombie",
    "was struck by lightning",
    "impaled",
    "squashed",
    "went up in flames",
    "flames",
    "didn't want to live",
    "skewered",
    "walked into fire",
    "went off with a bang",
    "walked into the danger zone",
    "was killed by magic",
    "froze to death",
    "was fireballed",
    "obliterated",
    "starved"
]

# BANNER

def create_banner():
    banner = f"""
       _____ ____  __ __ _____       ______                        
      / ___// __ \/ //_//  _/ |     / /  _/                        
      \__ \/ / / / ,<   / / | | /| / // /                          
     ___/ / /_/ / /| |_/ /  | |/ |/ // /                           
    /_____\______/ |_/___/  |__/|__/___/ 
                                            ______     __  ________
       /  |/  (_)___  ___  ______________ _/ __/ /_   / / / / ____/
      / /|_/ / / __ \/ _ \/ ___/ ___/ __ `/ /_/ __/  / /_/ / /     
     / /  / / / / / /  __/ /__/ /  / /_/ / __/ /_   / __  / /___   
    /_/  /_/_/_/ /_/\___/\___/_/   \__,_/_/  \__/  /_/ /_/\____/   
    """

    print(GREEN + banner + RESET)

# STATS
def load_stats():
    if not STATS_FILE.exists():
        return {
            "total_attempts": 0,
            "deaths": 0,
            "longest_game": 0,
            "furthest_progress": 0,
            "total_time": 0,
            "death types": {},
            "attempts": []
        }

    with open(STATS_FILE, "r") as file:
        return json.load(file)
    
def save_stats(stats):
    with open(STATS_FILE, "w") as file:
        json.dump(stats, file, indent=4)

# SERVER FUNCTIONS

def start_server():
    print("Starting Minecraft server...")

    process = subprocess.Popen(
        JAVA_COMMAND,
        cwd=SERVER_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    return process

def stop_server(process):
    print("Stopping Minecraft server...")
    try:
        process.stdin.write("stop\n")
        process.stdin.flush()

        process.wait()
    except:
        pass

def check_eula_agreement():
    print("Checking Eula agreement")
    eula = False
    try:
        with open(SERVER_DIR / "eula.txt", "r") as file:
            for line in file:
                if line.strip() == "eula=true":
                    eula = True
        eula = False
    except FileNotFoundError:
        eula = False

    if eula == False:
        print("Setting Eula to true")
        try:
            shutil.rm(SERVER_DIR / "eula.txt")
        except:
            print("error with removing eula")
            pass

        with open(SERVER_DIR /  "eula.txt","w") as eula:
            eula.write("eula=true") 

def enable_hardcore_mode():
    file_path = SERVER_DIR / "server.properties"
    temp_file_path = SERVER_DIR / "temp.properties"
    hardcore_key = "hardcore=false"
    hardcore_new = "hardcore=true"

    with open(file_path, "r") as input_file, open(temp_file_path, "w") as temp_file:
        for line in input_file:
            if line.strip() == hardcore_key:
                line = hardcore_new + "\n"
            temp_file.write(line)

    # Replace the original file with the temporary file
    os.replace(temp_file_path, file_path)
    print(GREEN + "[+]\tHardcore has been enabled in the server properties." + RESET)


# MINECRAFT FUNCTIONS
"""
Handle new players

Handle player input
Track When a player dies
- I want to track deaths first
- I want to track length of playing
- Check against longest play time
- track death types

track attempts
"""

def monitor_server(process, stats):
    current_players = []
    last_time_check = time.time()\

    for line in process.stdout:
        print(line, end="")

        # Check server has started
        if "Done" in line:
            process.stdin.write("scoreboard objectives add timesDied dummy\n")
            process.stdin.write("scoreboard objectives setdisplay list timesDied\n")
            process.stdin.flush()

        # Check Minecraft day every 10 seconds

        if time.time() - last_time_check >= 10:
            get_day(process)
            last_time_check = time.time()

        # Check time
        match = re.search(r"Timeline minecraft:day is at (\d+)", line)

        if match:
            print("GETTING TIME")
            day = int(match.group(1))
            stats["total_time"] += day
            if day > stats["longest_game"]:
                stats["longest_game"] = day
            for user in current_players:
                if stats["players"][user]["longest_game"] < day:
                    stats["players"][user]["longest_game"] = day
            save_stats(stats)

        # Handle new players joining
        match = re.search(r"(\w+) joined the game", line)

        if match:
            player = match.group(1)
            print(f"{player} has joined the game")
            if player not in stats["players"]:
                print_mc(process, f"Welcome {player} may the mines be the in your favour")
                stats["players"][player] = new_player()
                save_stats(stats)

            current_players.append(player)

            process.stdin.write(f"scoreboard players set {player} timesDied {stats['players'][player]['deaths']}\n")
            process.stdin.flush()
            print_player_stats(process, player, stats)

        # Handle players leaving
        match = re.search(r"(\w+) left the game", line)

        if match:
            player = match.group(1)
            print_mc(process, f"{player} tis a pussy for leaving the game")

            if player in current_players:
                current_players.remove(player)
        
        # Handle Player Commands
        match = re.search(r"\<(\w+)\> (.+)", line)

        if match:
            player = match.group(1)
            message = match.group(2)

            if not message.startswith("!"):
                continue

            command = message[1:]  # Remove the "!" prefix

            handle_command(player, command, process, stats)

        # Handle Death
        if any(death_message in line for death_message in death_messages):
            user = next((player for player in current_players if player in line), None)
            print_mc(process, f"Uh oh {user} is dead, bye bye world, bye bye diamonds, hello void, I think you're gonna die")

            get_day(process)
            player_died(user, stats)

            time.sleep(5)  # Wait for a few seconds before resetting the world
            return "DEATH", stats



    return None, stats

def handle_command(player, command, server, stats):
    if command == "stats":
        print_player_stats(server, player, stats)
    elif command == "time":
        get_day(server)
    elif command == "op":
        server.stdin.write(f"op {player}\n")
        server.stdin.flush()
    elif command == "help":
        print_mc(server, f"Available commands: !stats, !help")
    else:
        print_mc(server, f"Unknown command: {command}")

def get_day(server):
    server.stdin.write("time query day\n")
    server.stdin.flush()

    
def print_mc(server, msg):
    server.stdin.write(f"say {msg}\n")
    server.stdin.flush()

def new_player():
    return {
        "total_attempts": 0,
        "deaths": 0,
        "longest_game": 0,
        "furthest_progress": 0,
        "total_time": 0,
        "death types": {},
    }

def print_player_stats(server, player, stats):
    print_mc(server, f"Stats for {player}:")
    print_mc(server, f"Total Attempts: {stats['players'][player]['total_attempts']}")
    print_mc(server, f"Deaths: {stats['players'][player]['deaths']}")
    print_mc(server, f"Longest Game: {stats['players'][player]['longest_game']}")
    print_mc(server, f"Furthest Progress: {stats['players'][player]['furthest_progress']}")
    print_mc(server, f"Total Time: {stats['players'][player]['total_time']}")
    print_mc(server, "Death Types:")
    for death_type, count in stats['players'][player]['death types'].items():
        print_mc(server, f"  {death_type}: {count}")

def new_attmpt():
    return {
        "attempt_number": 0,
    }

def player_died(player, stats):
    print(f"{player} died")
    stats["players"][player]["deaths"] += 1

    save_stats(stats)

def reset_world():
    if WORLD_DIR.exists():
        shutil.rmtree(WORLD_DIR)
        print("World deleted.")


# GAME FUNCTIONS
def handle_death(stats):
    print("Someone Died")
    stats["deaths"] += 1
    stats["total_attempts"] += 1

    time.sleep(5)  # Wait for a few seconds before resetting the world

    reset_world()


# MAIN LOOP
def main():
    ## Main loop
    """
    When first started it needs to launch the server using the start server function
    Then monitor that server for events if a death even happens kill the world and server and restart
    Else stop the server
    """

    stats = load_stats()

    create_banner()

    while True:
        server = start_server()
        check_eula_agreement()
        enable_hardcore_mode()

        try:
            event, stats = monitor_server(server, stats)
        except KeyboardInterrupt:
            print("Interrupted by user")
            stop_server(server)
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            stop_server(server)
            sys.exit(0)

        stop_server(server)

        if event == "DEATH":
            handle_death(stats)

        save_stats(stats)
 
main()
