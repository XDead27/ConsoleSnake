import time
#from art import *
import curses
import importlib
from Maps.map import Map
from Resources.field import Field
import Resources.fruits as frt


class Duel(Map):
    def __init__(self):
        super(Duel, self).__init__()

        self.field = Field(17, 38, 0, '  ')
        self.p1 = self.field.addPerimeter(8, 8, [0, 0], -1, 's', 31)
        self.p2 = self.field.addPerimeter(8, 8, [0, 17], -1, 's', 31)
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
        fs11.setMaxFruits(1)
        fs11.setFruitRarity(0.01)

        fs12 = frt.FruitSpawner(frt.ObstacleFruit)
        fs12.bindAreaToPerimeter(self.p2)
        fs12.setMaxFruits(1)
        fs12.setFruitRarity(0.01)

        #For standard fruits
        fs21 = frt.FruitSpawner(frt.Plus1Fruit)
        fs21.bindAreaToPerimeter(self.p1)
        fs21.setMaxFruits(1)
        fs21.setFruitRarity(1)

        fs22 = frt.FruitSpawner(frt.Plus1Fruit)
        fs22.bindAreaToPerimeter(self.p2)
        fs22.setMaxFruits(1)
        fs22.setFruitRarity(1)

        fs31 = frt.FruitSpawner(frt.TeliprtFruit)
        fs31.bindAreaToPerimeter(self.p1)
        fs31.setMaxFruits(1)
        fs31.setFruitRarity(0.008)

        fs32 = frt.FruitSpawner(frt.TeliprtFruit)
        fs32.bindAreaToPerimeter(self.p2)
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

    def getSpecificColors(self):
        specific_colors = super(Duel, self).getSpecificColors() 
        specific_colors.extend([
            {"number": 30, "fg": "black", "bg": "black"},
            {"number": 31, "fg": "white", "bg": "black"}
        ])
        return specific_colors

    def incrementPerimeters(self):
        if self.p1.width + self.p1.position[1] < self.field.width and self.p1.height + self.p1.position[0] < self.field.height and \
           self.p2.width + self.p2.position[1] < self.field.width and self.p2.height + self.p2.position[0] < self.field.height:
            self.field.resizePerimeter(self.p1, self.p1.height + 1, self.p1.width + 1)
            self.field.resizePerimeter(self.p2, self.p2.height + 1, self.p2.width + 1)
        else:
            self.field.addSegment([self.p1.position[0] + 1, self.p1.position[1] + self.p1.width - 1], [self.p1.position[0] + self.p1.height - 2, self.p1.position[1] + self.p1.width - 1], 0, '  ', 30)
            self.field.addSegment([self.p2.position[0] + 1, self.p2.position[1]], [self.p2.position[0] + self.p2.height - 2, self.p2.position[1]], 0, '  ', 30)
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
