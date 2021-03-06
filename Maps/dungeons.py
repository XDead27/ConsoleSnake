from hashlib import new
import time
import curses
import math
from random import randrange
from Maps.map import Map
from Resources.field import Field, Perimeter
import Resources.fruits as frt
from Resources.utils import isInRange

##This has to be the hardest shit to do jesus christ
#A procedurally generated map on a field that is as big as possible
class Dungeons(Map):
    #Specific to this map
    MIN_PER_DIM = 5
    MAX_PER_DIM = 20
    DEFAULT_SIZE = 40
    
    def __init__(self):
        super(Dungeons, self).__init__()

        self.height = self.width = self.DEFAULT_SIZE

        self.reset()

        self.maxPlayers = 4
        

    def reset(self):
        super(Dungeons, self).reset()
        self.field = Field(self.height + 1, self.height + 1, 0, '  ')
        self.perimeter = self.field.addPerimeter(self.height, self.width, [0, 0], -2, 'm', 31)
        self.obstacles.append(self.perimeter)

        #Setup spawners
        # fs1 = frt.FruitSpawner(frt.AbundanceFruit)
        # fs1.bindAreaToPerimeter(self.p1)
        # fs1.setMaxFruits(2)
        # fs1.setFruitRarity(0.2)

        # fs2 = frt.FruitSpawner(frt.TeliprtFruit)
        # fs2.bindAreaToPerimeter(self.p1)
        # fs2.setMaxFruits(1)
        # fs2.setFruitRarity(0.002)

        self.field.setDimensions(self.height, self.width)
        self.field.reset()
        self.field.resizePerimeter(self.perimeter, self.height, self.width)
        
        #Starting perimeters
        start1 = self.field.addPerimeter(8, 8, [0, 0], -1, 's', 31)
        start2 = self.field.addPerimeter(8, 8, [self.field.height - 8, 0], -1, 's', 31)
        start3 = self.field.addPerimeter(8, 8, [0, self.field.width - 8], -1, 's', 31)
        start4 = self.field.addPerimeter(8, 8, [self.field.height - 8, self.field.width - 8], -1, 's', 31)
        self.obstacles.append(start1)
        self.obstacles.append(start2)
        self.obstacles.append(start3)
        self.obstacles.append(start4)

        self.createMap()

        self.lastNumberOfFruits = [0] * len(self.fruitSpawners)

        self.spawnLocations = [[1, 1],[1, self.field.width - 7], [self.field.height - 7, 1], [self.field.height - 7, self.field.width - 7]]

    def getSpecificColors(self):
        specific_colors = super(Dungeons, self).getSpecificColors() 
        specific_colors.extend([
            {"number": 31, "fg": "red", "bg": "black"},
            {"number": 32, "fg": "white", "bg": "black"}
        ])
        return specific_colors

    def getSpecificOptions(self):
        opt = super(Dungeons, self).getSpecificOptions()

        new_opt = {
            "height": self.height,
            "width": self.width
        }

        opt.update(new_opt)

        return opt

    def setOptions(self, options={}):
        super(Dungeons, self).setOptions(options)
        if options.get("height"):
            self.height = self.DEFAULT_SIZE if int(options.get("height")) <= 4 else int(options.get("height"))

        if options.get("width"):
            self.width = self.DEFAULT_SIZE if int(options.get("width")) <= 4 else int(options.get("width"))

        self.reset()
        
    #Refactor Refactor Refactor
    def createMap(self):
        #We spawn the perimeters, checking not to overlap eachother
        MAX_TRIES = 140
        full = False
        
        #Get list of perimeters
        pers = []
        for obs in self.obstacles:
            if isinstance(obs, Perimeter) and not obs == self.perimeter:
                pers.append(obs)
        
        while not full:
            #Get random coordinates for our new perimeter
            per_pos = [randrange(1, self.field.height - 1), randrange(1, self.field.width - 1)]
            per_height = randrange(self.MIN_PER_DIM, self.MAX_PER_DIM)
            per_width = randrange(self.MIN_PER_DIM, self.MAX_PER_DIM)
            
            tries = 0
            while True:
                valid = True
                
                #Dummy perimeter to access the functions
                temp_per = Perimeter(per_height, per_width, per_pos, 0, '  ', 1)
                for perimeter in pers:
                    for corner in temp_per.getCorners():
                        if isInRange(corner, perimeter.position, perimeter.getEnd()):
                            valid = False
                            break
                        
                    for corner in perimeter.getCorners():
                        if isInRange(corner, temp_per.position, temp_per.getEnd()):
                            valid = False
                            break
                        
                    if not valid:
                        break
                    
                if valid:
                    new_per = self.field.addPerimeter(per_height, per_width, per_pos, -3, 'o', 32)
                    if new_per == -1:
                        break
                    self.obstacles.append(new_per)
                    pers.append(new_per)
                    break
                elif tries >= MAX_TRIES:
                    full = True
                    break
                else:
                    per_pos = [randrange(1, self.field.height - 1), randrange(1, self.field.width - 1)]
                    per_height = randrange(self.MIN_PER_DIM, self.MAX_PER_DIM)
                    per_width = randrange(self.MIN_PER_DIM, self.MAX_PER_DIM)
                
                tries += 1
                
        self.field.refresh()
                
        # We create the bridges, as follows
        ## randomly pick a starting point on the outer edge of an perimeter
        ## randomly pick a slope
        ## start checking, step by step, the sqares that complete the line with that slope
        ## when reaching another wall, mark that as the endpoint
        ## build a bridge from 2 obstacle segments and one blank segment with the same slope and different offsets


    def update(self):
        super(Dungeons, self).update()
