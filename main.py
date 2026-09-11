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

allowed_death_entities = [
    "Named entity class",
    "entity class",
    "class_1646",
    "*"
]

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


advancements = {
    "Stone Age": 1,
    "Acquire Hardware": 2,
    "Hot Stuff": 3,
    "Diamonds!": 4,
    "Ice Bucket Challenge": 5,
    "We Need to Go Deeper": 6,
    "Nether": 7,
    "A Terrible Fortress": 8,
    "Eye Spy": 9,
    "The End?": 10,
    "Or the beginning?": 11,
    "Free the End": 12,
}

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
            "attempts": {},
            "longest_run": 0,
            "total_run_time": 0,
            "furthest_progress": 0,
            "current_run": {},
            "deaths": {},
            "players": {}
            
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
    progress = stats["current_run"].get("progress", 0)
    server_started = False

    for line in process.stdout:
        print(line, end="")

        # Check server has started
        if "Done" in line and not server_started:
            process.stdin.write("scoreboard objectives add timesDied dummy\n")
            process.stdin.write("scoreboard objectives setdisplay list timesDied\n")
            process.stdin.flush()
            server_started = True

        # Handle new players joining
        match = re.search(r"(\w+) joined the game", line)

        if match:
            player = match.group(1)
           
            if player not in stats["players"]:
                print_mc(process, f"Welcome {player} may the mines be the in your favour")
                stats["players"][player] = new_player()
                save_stats(stats)
            if player not in stats["current_run"]["players"]:
                stats["current_run"]["players"].append(player)
                save_stats(stats)
                print_mc(process, f"{player} has joined the current run")

            current_players.append(player)

            process.stdin.write(f"scoreboard players set {player} timesDied {stats['players'][player]['deaths_total']}\n")
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

        # Handle Advancment
        match = re.match(r"(.+) has made the advancement \[(.+)\]", line)

        if match:
            player = match.group(1)
            advancement = match.group(2)

            if advancement in advancements:
                lvl = advancements[advancement]
                if progress < lvl:
                    progress = lvl
                    stats["current_run"]["progress"] = progress
                    print(f"{player} reached progress {progress}")
                    save_stats(stats)


        # Handle Death
        """
        Update all stats
        get death type then
        Update the deaths and add a death to the player that died
        get final run time and final run progress and update run / players and overall time stat
        Check if this is the longest run and update if so on player / overall
        Check if furthest progress and update if so on player / overall
        update the attempts for all players on this run

        save the current run in attempts
        clear the current run
        """

        if any(death_message in line for death_message in death_messages):
            user = next((player for player in current_players if player in line), None)
            death_message = next((death_message for death_message in death_messages if death_message in line), None)

            if not any(f"<{username}>" in line for username in current_players) and not "[Server]" in line and not any(death_entities in line for death_entities in allowed_death_entities):

                # Warn server of death
                print_mc(process, f"Uh oh {user} is dead,\n bye bye world,\nbye bye diamonds, \nhello void, \nI think you're gonna die")

                #Handle deaths]
                stats["deaths"][death_message] = stats["deaths"].get(death_message, 0) + 1

                # Handle day
                day = get_day(process)

                # Handle progress
                progress = stats["current_run"].get("progress", 0)
                if stats["furthest_progress"] < progress:
                    print(f"New furthest progress: {progress}")
                    stats["furthest_progress"] = progress

                # current run
                current_run = stats["current_run"]

                current_run["length"] = day
                current_run["progress"] = progress
                current_run["death_type"] = death_message
                current_run["who_died"] = user

                stats["current_run"] = current_run

                # Handle death
                stats = player_died(user, stats, ticks=day, progress=progress, death_type=death_message, attempt=stats["current_run"])

                #clear current run
                stats["current_run"] = {}

                save_stats(stats)
                
                print_mc(process, f"The world will be deleted now, sorry")
                time.sleep(1)  
                print_mc(process, f"3")
                time.sleep(1)  
                print_mc(process, f"2")
                time.sleep(1) 
                print_mc(process, f"1")
                time.sleep(1) 
                print_mc(process, f"Goodbye world")
                time.sleep(1) 

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

    while True:
        line = server.stdout.readline()

        match = re.search(r"Timeline minecraft:day is at (\d+)", line)

        if match:
            return int(match.group(1))

    
def print_mc(server, msg):
    server.stdin.write(f"say {msg}\n")
    server.stdin.flush()

def new_player():
    return {
        "total_attempts": 0,
        "attempts": {},
        "deaths_total": 0,
        "deaths": {},
        "longest_run": 0,
        "total_run_time": 0,
        "furthest_progress": 0
    }

def new_attempt(num):
    return {
        "attempt_number": num,
        "length": 0,
        "progress": 0,
        "death_type": "",
        "who_died": "",
        "players": []
    }

def print_player_stats(server, player, stats):
    print_mc(server, f"Stats for {player}:")
    print_mc(server, f"Total Attempts: {stats['players'][player]['total_attempts']}")
    print_mc(server, f"Deaths: {stats['players'][player]['deaths_total']}")
    print_mc(server, f"Longest Game: {ticks_to_real_time(stats['players'][player]['longest_run'])}")
    print_mc(server, f"Furthest Progress: {stats['players'][player]['furthest_progress']}")
    print_mc(server, f"Total Time: {stats['players'][player]['total_run_time']}")
    #print_mc(server, "Death Types:")
    #for death_type, count in stats['players'][player]['deaths'].items():
    #    print_mc(server, f"  {death_type}: {count}")



def player_died(player, stats, ticks=0, progress=0, death_type="", attempt=None):
    # Overall  
    stats["total_attempts"] += 1

    stats["attempts"][stats["total_attempts"]] = attempt

    #time
    stats["total_run_time"] += ticks

    if ticks > stats["longest_run"]:
        print(f"New longest run: {ticks_to_real_time(ticks)} ticks")
        stats["longest_run"] = ticks

    if progress > stats["furthest_progress"]:
        print(f"New furthest progress: {progress}")
        stats["furthest_progress"] = progress

    for p in stats["current_run"]["players"]:
        stats["players"][p]["total_attempts"] += 1
        stats["players"][p]["attempts"][stats["total_attempts"]] = attempt

        stats["players"][p]["total_run_time"] += ticks

        if ticks > stats["players"][p]["longest_run"]:
            print(f"New longest game for {p}: {ticks_to_real_time(ticks)}")
            stats["players"][p]["longest_run"] = ticks

        if stats["players"][p]["furthest_progress"] < progress:
            print(f"New furthest progress for {p}: {progress}")
            stats["players"][p]["furthest_progress"] = progress

        if player == p:
            stats["players"][p]["deaths_total"] += 1
        stats["players"][p]["deaths"][death_type] = (
            stats["players"][p]["deaths"].get(death_type, 0) + 1
        )
    return stats
        

def ticks_to_real_time(ticks: int) -> str:
    """Converts Minecraft game ticks into real-world human time duration (HH:MM:SS)."""
    # Minecraft runs at 20 ticks per second
    total_seconds = ticks // 20
    
    # Calculate hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    # Return formatted string with zero-padding (e.g., 01:23:45)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# GAME FUNCTIONS
def reset_world():
    if WORLD_DIR.exists():
        shutil.rmtree(WORLD_DIR)
        print("World deleted.")


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
        check_eula_agreement()
        enable_hardcore_mode()

        server = start_server()

        if stats["current_run"] == {}:
            stats["current_run"] = new_attempt(stats["total_attempts"] + 1)
            save_stats(stats)

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
            reset_world()

        save_stats(stats)
 
main()
