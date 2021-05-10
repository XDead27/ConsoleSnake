import time
from art import *
import sys
import curses
from random import randrange
sys.path.insert(1, '/home/mrxdead/Documents/Projects/ConsoleSnake')
from Maps.map import Map
from field import Field
import fruits as frt


class Survival(Map):
    def __init__(self):
        super(Survival, self).__init__()

        #Colors for our map
        curses.init_pair(100, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(101, curses.COLOR_WHITE, curses.COLOR_BLACK)

        self.field = Field(20, 20, 0, '  ')
        self.p1 = self.field.addPerimeter(20, 20, [0, 0], -1, 's', 101)
        self.obstacles.append(self.p1)

        #Specific to this map
        self.coords = []
        self.iters = 0
        self.DEFAULT_SIZE = 15

        #Setup spawners
        fs1 = frt.FruitSpawner(frt.Plus1Fruit)
        fs1.bindAreaToPerimeter(self.p1)
        fs1.setMaxFruits(2)
        fs1.setFruitRarity(0.2)

        fs2 = frt.FruitSpawner(frt.TeliprtFruit)
        fs2.bindAreaToPerimeter(self.p1)
        fs2.setMaxFruits(1)
        fs2.setFruitRarity(0.002)

        self.fruitSpawners.append(fs1)
        self.fruitSpawners.append(fs2)

        self.lastNumberOfFruits = [0] * len(self.fruitSpawners)

        self.maxPlayers = 4
        self.spawnLocations = [[1, 1], [3, 3], [5, 5], [7, 7]]

    def askForParams(self, stdscr):
        super(Survival, self).askForParams(stdscr)
        curses.flushinp()
        curses.nocbreak()
        stdscr.nodelay(False)
        stdscr.addstr("Size (height): ")
        stdscr.refresh()
        h = stdscr.getstr(1, 0, 3).decode("utf-8")
        stdscr.addstr("Size (width): ")
        w = stdscr.getstr(3, 0, 3).decode("utf-8")

        h = self.DEFAULT_SIZE if h == '' else int(h)
        w = self.DEFAULT_SIZE if w == '' else int(w)

        self.field.setDimensions(h + 1, w + 1)
        self.field.reset()
        self.field.shapes.remove(self.p1)
        self.p1 = self.field.addPerimeter(h, w, [0, 0], -1, 's', 101)
        self.field.refresh()

        for fs in self.fruitSpawners:
            fs.bindAreaToPerimeter(self.p1)

        curses.cbreak()
        stdscr.nodelay(True)

    def playIntro(self, stdscr):
        super(Survival, self).playIntro("Survival", "defleppard", stdscr)

    def clearObstacles(self):
        for x in self.coords:
            self.field.clearTempNumAt(x)
        self.coords = []

    def calculateRarity(self, turn):
        return 30/(turn+30)

    def update(self):
        self.iters += 1
        if self.iters % 2 == 0:
            x = [randrange(1, self.field.height - 1), randrange(1, self.field.width - 1)]
            while not self.field.getNumAt(x) == self.field.blank_number:
                x = [randrange(1, self.field.height - 1), randrange(1, self.field.width - 1)]

            self.field.addTempNumAt(x, -1, 's', 101)
            self.coords.append(x)

        for i in range(len(self.fruitSpawners)):
            condition = self.lastNumberOfFruits[i] > len(self.fruitSpawners[i].spawnedFruits)
            if condition:
                self.clearObstacles()
            self.fruitSpawners[i].spawnInField(self.field)
            self.lastNumberOfFruits[i] = len(self.fruitSpawners[i].spawnedFruits)
            self.fruitSpawners[0].setFruitRarity(self.calculateRarity(self.iters))
