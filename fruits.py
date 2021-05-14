from random import randrange
import random
from field import Segment, Perimeter

class FruitSpawner():
    def __init__(self, fruitType):
        self.fruitType = []
        self.fruitType.append(fruitType)
        self.maxFruits = 1
        self.maxSpawns = 0
        self.totalFruits = 0
        self.fruitRarity = 1
        self.spawnedFruits = []
        self.bindedPerimeter = None

    def setFruitAesthetics(self, number, string, color):
        self.fruitNumber = number
        self.fruitString = string
        self.fruitColor = color

    def setFruitRarity(self, rarity):
        self.fruitRarity = rarity

    def setFruitType(self, ft):
        self.fruitType = []
        self.fruitType.extend(ft)

    def setSpawnArea(self, spawnStart, spawnEnd):
        self.spawnStart = spawnStart
        self.spawnEnd = spawnEnd

    def bindAreaToPerimeter(self, per):
        self.bindedPerimeter = per
        self.spawnStart = [self.bindedPerimeter.position[0] + 1, self.bindedPerimeter.position[1] + 1]
        self.spawnEnd = [self.bindedPerimeter.position[0] + self.bindedPerimeter.height - 2, self.bindedPerimeter.position[1] + self.bindedPerimeter.width - 2]

    def setMaxFruits(self, n):
        self.maxFruits = n

    def setMaxSpawns(self, m):
        self.maxSpawns = m

    def getSpawnLocation(self):
        if self.bindedPerimeter:
            self.spawnStart = [self.bindedPerimeter.position[0] + 1, self.bindedPerimeter.position[1] + 1]
            self.spawnEnd = [self.bindedPerimeter.position[0] + self.bindedPerimeter.height - 2, self.bindedPerimeter.position[1] + self.bindedPerimeter.width - 2]

        if random.uniform(0, 1) <= self.fruitRarity:
            return [randrange(self.spawnStart[0], self.spawnEnd[0]), randrange(self.spawnStart[1], self.spawnEnd[1])]
        else:
            return False

    def spawnInField(self, field):
        if (not self.maxSpawns == 0 and self.totalFruits > self.maxSpawns) or len(self.spawnedFruits) >= self.maxFruits:
            return

        spawnTo = self.getSpawnLocation()
        tries = 1

        while spawnTo and not field.getNumAt(spawnTo) == field.blank_number and not tries > 100:
            spawnTo = self.getSpawnLocation()
            tries += 1

        if spawnTo:
            newFruit = self.fruitType[randrange(len(self.fruitType))](spawnTo)
            self.spawnedFruits.append(field.appendSegment(newFruit))
            self.totalFruits += 1

class Fruit(Segment):
    def __init__(self, pos, number, string, color):
        super(Fruit, self).__init__(pos, pos, number, string, color)
        self.description = ''

    def doMagic(self, s, otherSnakes, map):
        #magic to be added
        pass

class Plus1Fruit(Fruit):
    def __init__(self, pos, number = 1, string = 'x', color = 9):
        super(Plus1Fruit, self).__init__(pos, number, string, color)
        self.description = 'Just adds 1 to the length of the snaek. Kinda basic.'

    def doMagic(self, s, otherSnakes, map):
        s.length += 1

class TeliprtFruit(Fruit):
    def __init__(self, pos, number = 2, string = 'o', color = 10):
        super(TeliprtFruit, self).__init__(pos, number, string, color)
        self.description = 'Do the teliprrrt. How ?!.?'

    def doMagic(self, s, otherSnakes, map):
        p = map.field.shapes[randrange(0, len(map.field.shapes))]

        while not isinstance(p, Perimeter):
            p = map.field.shapes[randrange(0, len(map.field.shapes))]

        teleportTo = [p.position[0] + randrange(2, p.height - 3), p.position[1] + randrange(2, p.width - 3)]

        while not map.field.getNumAt(teleportTo) == map.field.blank_number:
            teleportTo = [p.position[0] + randrange(2, p.height - 3), p.position[1] + randrange(2, p.width - 3)]

        s.head = teleportTo

class ObstacleFruit(Fruit):
    def __init__(self, pos, number = 3, string = 'D', color = 11):
        super(ObstacleFruit, self).__init__(pos, number, string, color)
        self.description = 'Block your enemy or yourself. Such strategy!'

    def doMagic(self, s, otherSnakes, map):
        p = map.field.shapes[randrange(0, len(map.field.shapes))]

        while not isinstance(p, Perimeter):
            p = map.field.shapes[randrange(0, len(map.field.shapes))]

        start = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        while not map.field.getNumAt(start) == map.field.blank_number:
            start = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        end = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        while not map.field.getNumAt(end) == map.field.blank_number:
            end = [p.position[0] + randrange(1, p.height - 1), p.position[1] + randrange(1, p.width - 1)]

        newSegment = map.field.addSegment(start, end, -1, 's', 101)

class Plus4Fruit(Fruit):
    def __init__(self, pos, number = 4, string = 'x', color = 12):
        super(Plus4Fruit, self).__init__(pos, number, string, color)
        self.description = '4 points are better than one. Almost always'

    def doMagic(self, s, otherSnakes, map):
        s.length += 4

class AbundanceFruit(Fruit):
    def __init__(self, pos, number = 5, string = 'A', color = 13):
        super(AbundanceFruit, self).__init__(pos, number, string, color)
        self.description = 'Fruits will start to flourish around you and chaos will reign supreme!'

    def doMagic(self, s, otherSnakes, map):
        #This is what a poor man has to do to get a reference to this fruit's spawner :(
        for fs in map.fruitSpawners:
            if self in fs.spawnedFruits:
                thisFs = fs
                
        #Chaos level
        chaos_level = 15
                
        #Record initial state of the fruit spawner
        init_type = thisFs.fruitType
        init_maxFruits = thisFs.maxFruits
        init_maxSpawns = thisFs.maxSpawns
        init_rarity = thisFs.fruitRarity
        
        #Get current spawns and fruits
        curr_spawns = thisFs.totalFruits
        curr_fruits = len(thisFs.spawnedFruits)

        thisFs.setFruitType([Plus1Fruit, Plus4Fruit, TeliprtFruit, ObstacleFruit])
        thisFs.setMaxFruits(chaos_level + curr_fruits)
        thisFs.setMaxSpawns(chaos_level + 1 + curr_spawns)
        thisFs.setFruitRarity(1)
        
        for i in range(chaos_level):
            thisFs.spawnInField(map.field)
        
        #Reset overloaded fruit spawner
        thisFs.setFruitType(init_type)
        thisFs.setMaxFruits(init_maxFruits)
        thisFs.setMaxSpawns(init_maxSpawns)
        thisFs.setFruitRarity(init_rarity)
        thisFs.totalFruits = curr_spawns
            
        
            
        
