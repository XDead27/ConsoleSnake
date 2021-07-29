from art import tprint, text2art
import time
import os
import curses
import random

class Map:
    def __init__(self):
        self.field = None
        self.obstacles = []
        self.fruitSpawners = []
        self.maxPlayers = 0
        self.spawnLocations = []
        self.refreshRate = 0.5

    def getDetails(self):
        fruit_details = []
        alreadyMentioned = []
        for fs in self.fruitSpawners:
            name = fs.fruitType[0].__name__
            if name not in alreadyMentioned:
                fruit = fs.fruitType[0]([0, 0])
                char = fruit.string
                desc = fruit.description

                details = {}
                details["name"] = name
                details["char"] = char
                details["description"] = desc

                fruit_details.append(details)
                alreadyMentioned.append(name)
        return fruit_details

    def getSpecificColors(self):
        pass
    
    # def askForParams(self, stdscr):
    #     pass

    def update(self):
        #Spawn thee fruits
        for f in self.fruitSpawners:
            f.spawnInField(self.field)

    def getRandomSpawnLocation(self, i):
        return self.spawnLocations[i]

# Methods for displaying map info (client-side)
def playIntro(map_name):
    try:
        displayTitle(map_name)
        # TODO: Add this functionality
        # askForParams(stdscr)
        countdown()

    except KeyboardInterrupt:
        tprint("...Weakling")
        time.sleep(1)
        curses.nocbreak()
        curses.endwin()
        os._exit(0)

# List of fonts for the map display (client-side)
map_fonts = {
    "classic": {"name":"CLASSIC", "font":"pawp"},
    "duel": {"name":"DUEL", "font":"sub-zero"},
    "survival": {"name":"Survival", "font":"defleppard"},
    "dungeons": {"name":"Dungeons", "font":"amcrazor"}
}

def displayTitle(map_name):
    name = map_fonts.get(map_name).get("name")
    font = map_fonts.get(map_name).get("font")

    tprint("You have chosen", font='thin')
    tprint(name, font=font)
    tprint("-----------")

def countdown():
    for x in range(3):
        tprint(str(3 - x))
        time.sleep(1)

def displayDetails(fruit_details):
    for details in fruit_details:
        print(text2art(details['char'], font='cjk') + "(" + details['name'] + ") - " + details['description'] + "\n")