import time
from art import *
import sys
import curses
sys.path.insert(1, '/home/mrxdead/Documents/Projects/ConsoleSnake')
from Maps.map import Map
from field import Field
import fruits as frt


class Duel(Map):
    def __init__(self):
        super(Duel, self).__init__()

        #Colors for our map
        curses.init_pair(100, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(101, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_GREEN, curses. COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_WHITE)
        curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_RED)
        curses.init_pair(11, curses.COLOR_RED, curses.COLOR_WHITE)

        self.field = Field(17, 38, 0, '  ')
        self.p1 = self.field.addPerimeter(8, 8, [0, 0], -1, 's', 101)
        self.p2 = self.field.addPerimeter(8, 8, [0, 17], -1, 's', 101)
        self.obstacles.append(self.p1)
        self.obstacles.append(self.p2)

        #Only for this map
        self.extended = False
        self.fruitsEaten = 0
        self.refreshIncrement = 0.02

        ##This should be rethinked as I am unable to can
        #Note from future: I really do not want to refactor this
        #For Teliprt fruit
        fs11 = frt.FruitSpawner(frt.ObstacleFruit)
        fs11.bindAreaToPerimeter(self.p1)
        fs11.setFruitAesthetics(2, 'O', 9)
        fs11.setMaxFruits(1)
        fs11.setFruitRarity(0.01)

        fs12 = frt.FruitSpawner(frt.ObstacleFruit)
        fs12.bindAreaToPerimeter(self.p2)
        fs12.setFruitAesthetics(2, 'O', 9)
        fs12.setMaxFruits(1)
        fs12.setFruitRarity(0.01)

        #For standard fruits
        fs21 = frt.FruitSpawner(frt.Plus1Fruit)
        fs21.bindAreaToPerimeter(self.p1)
        fs21.setFruitAesthetics(1, 'x', 10)
        fs21.setMaxFruits(1)
        fs21.setFruitRarity(1)

        fs22 = frt.FruitSpawner(frt.Plus1Fruit)
        fs22.bindAreaToPerimeter(self.p2)
        fs22.setFruitAesthetics(1, 'x', 10)
        fs22.setMaxFruits(1)
        fs22.setFruitRarity(1)

        fs31 = frt.FruitSpawner(frt.TeliprtFruit)
        fs31.bindAreaToPerimeter(self.p1)
        fs31.setFruitAesthetics(3, 'D', 9)
        fs31.setMaxFruits(1)
        fs31.setFruitRarity(0.008)

        fs32 = frt.FruitSpawner(frt.TeliprtFruit)
        fs32.bindAreaToPerimeter(self.p2)
        fs32.setFruitAesthetics(3, 'D', 9)
        fs32.setMaxFruits(1)
        fs32.setFruitRarity(0.008)

        self.fruitSpawners.append(fs11)
        self.fruitSpawners.append(fs12)
        self.fruitSpawners.append(fs21)
        self.fruitSpawners.append(fs22)
        self.fruitSpawners.append(fs31)
        self.fruitSpawners.append(fs32)

        self.lastNumberOfFruits = [0] * len(self.fruitSpawners)

        self.maxPlayers = 2
        self.spawnLocations = [[1, 1], [1, 18]]

    def playIntro(self, stdscr):
        super(Duel, self).playIntro("Duel", "sub-zero", stdscr)

    def incrementPerimeters(self):
        if self.p1.width + self.p1.position[1] < self.field.width and self.p1.height + self.p1.position[0] < self.field.height and \
           self.p2.width + self.p2.position[1] < self.field.width and self.p2.height + self.p2.position[0] < self.field.height:
            self.field.resizePerimeter(self.p1, self.p1.height + 1, self.p1.width + 1)
            self.field.resizePerimeter(self.p2, self.p2.height + 1, self.p2.width + 1)
        else:
            self.field.addSegment([self.p1.position[0] + 1, self.p1.position[1] + self.p1.width - 1], [self.p1.position[0] + self.p1.height - 2, self.p1.position[1] + self.p1.width - 1], 0, '  ', 100)
            self.field.addSegment([self.p2.position[0] + 1, self.p2.position[1]], [self.p2.position[0] + self.p2.height - 2, self.p2.position[1]], 0, '  ', 100)
            self.extended = True

        self.refreshRate -= self.refreshIncrement

    def update(self):
        #In this map the perimeters extend after each fruit eaten
        for i in range(len(self.fruitSpawners)):
            condition = self.lastNumberOfFruits[i] > len(self.fruitSpawners[i].spawnedFruits)
            if condition and not self.extended:
                self.fruitsEaten += 1
            self.fruitSpawners[i].spawnInField(self.field)
            self.lastNumberOfFruits[i] = len(self.fruitSpawners[i].spawnedFruits)

        if self.fruitsEaten == 3:
            self.incrementPerimeters()
            self.fruitsEaten = 0
