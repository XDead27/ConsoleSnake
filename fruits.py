from random import randrange
import random
from field import Segment, Perimeter

class FruitSpawner():
    def __init__(self, fruitType):
        self.fruitType = fruitType
        self.maxFruits = 1
        self.fruitRarity = 1
        self.spawnedFruits = []
        self.bindedPerimeter = None

    def setFruitAesthetics(self, number, string, color):
        self.fruitNumber = number
        self.fruitString = string
        self.fruitColor = color

    def setFruitRarity(self, rarity):
        self.fruitRarity = rarity

    def setfruitType(self, ft):
        self.fruitType = ft

    def setSpawnArea(self, spawnStart, spawnEnd):
        self.spawnStart = spawnStart
        self.spawnEnd = spawnEnd

    def bindAreaToPerimeter(self, per):
        self.bindedPerimeter = per
        self.spawnStart = [self.bindedPerimeter.position[0] + 1, self.bindedPerimeter.position[1] + 1]
        self.spawnEnd = [self.bindedPerimeter.position[0] + self.bindedPerimeter.height - 2, self.bindedPerimeter.position[1] + self.bindedPerimeter.width - 2]

    def setMaxFruits(self, n):
        self.maxFruits = n

    def getSpawnLocation(self):
        if self.bindedPerimeter:
            self.spawnStart = [self.bindedPerimeter.position[0] + 1, self.bindedPerimeter.position[1] + 1]
            self.spawnEnd = [self.bindedPerimeter.position[0] + self.bindedPerimeter.height - 2, self.bindedPerimeter.position[1] + self.bindedPerimeter.width - 2]

        if random.uniform(0, 1) <= self.fruitRarity:
            return [randrange(self.spawnStart[0], self.spawnEnd[0]), randrange(self.spawnStart[1], self.spawnEnd[1])]
        else:
            return False

    def spawnInField(self, field):
        spawnTo = self.getSpawnLocation()

        while spawnTo and not field.getNumAt(spawnTo) == field.blank_number:
            spawnTo = self.getSpawnLocation()

        if spawnTo and len(self.spawnedFruits) < self.maxFruits:
            newFruit = self.fruitType(spawnTo, self.fruitNumber, self.fruitString, self.fruitColor)
            self.spawnedFruits.append(field.appendSegment(newFruit))

class Fruit(Segment):
    def __init__(self, pos, number, string, color):
        super(Fruit, self).__init__(pos, pos, number, string, color)
        self.description = ''

    def doMagic(self, s, f = None):
        #magic to be added
        pass

class Plus1Fruit(Fruit):
    def __init__(self, pos, number, string, color = 1):
        super(Plus1Fruit, self).__init__(pos, number, string, color)
        self.description = 'Just adds 1 to the length of the snaek. Kinda basic.'

    def doMagic(self, s, f = None):
        s.length += 1

class TeliprtFruit(Fruit):
    def __init__(self, pos, number, string, color = 1):
        super(TeliprtFruit, self).__init__(pos, number, string, color)
        self.description = 'Do the teliprrrt. How ?!.?'

    def doMagic(self, s, f):
        p = f.shapes[randrange(0, len(f.shapes))]

        while not isinstance(p, Perimeter):
            p = f.shapes[randrange(0, len(f.shapes))]

        teleportTo = [p.position[0] + randrange(2, p.height - 3), p.position[1] + randrange(2, p.width - 3)]

        while not f.getNumAt(teleportTo) == f.blank_number:
            teleportTo = [p.position[0] + randrange(2, p.height - 3), p.position[1] + randrange(2, p.width - 3)]

        s.head = teleportTo

class ObstacleFruit(Fruit):
    def __init__(self, pos, number, string, color = 1):
        super(ObstacleFruit, self).__init__(pos, number, string, color)
        self.description = 'Block your enemy or yourself. Such strategy!'

    def doMagic(self, s, f):
        p = f.shapes[randrange(0, len(f.shapes))]

        while not isinstance(p, Perimeter):
            p = f.shapes[randrange(0, len(f.shapes))]

        start = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        while not f.getNumAt(start) == f.blank_number:
            start = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        end = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        while not f.getNumAt(end) == f.blank_number:
            end = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        newSegment = f.addSegment(start, end, -1, 's', 101)
