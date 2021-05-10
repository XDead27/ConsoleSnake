from art import *
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

    def displayTitle(self, name, font, stdscr):
        tprint("You have chosen", font='thin')
        tprint(name, font=font)
        tprint("-----------")

    def displayDetails(self, stdscr):
        print("Types of fruits in this gamemode:\n")
        alreadyMentioned = []
        for fs in self.fruitSpawners:
            name = fs.fruitType[0].__name__
            if name not in alreadyMentioned:
                fruit = fs.fruitType[0]([0, 0])
                char = fruit.string
                desc = fruit.description
                print(text2art(char, font='cjk') + "(" + name + ") - " + desc + "\n")
                alreadyMentioned.append(name)

    def askForParams(self, stdscr):
        pass

    def countdown(self):
        for x in range(3):
            tprint(str(3 - x))
            time.sleep(1)

    def playIntro(self, name, font, stdscr):
        try:
            self.displayTitle(name, font, stdscr)
            self.askForParams(stdscr)
            self.countdown()

        except KeyboardInterrupt:
            tprint("...Weakling")
            time.sleep(1)
            curses.nocbreak()
            curses.endwin()
            os._exit(0)

    def update(self):
        #Spawn thee fruits
        for f in self.fruitSpawners:
            f.spawnInField(self.field)

    def getRandomSpawnLocation(self, i):
        return self.spawnLocations[i]
