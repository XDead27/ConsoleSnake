import time
import curses
from Maps.map import Map
from Resources.field import Field
import Resources.fruits as frt


class Classic(Map):
    DEFAULT_SIZE = 12
    def __init__(self):
        super(Classic, self).__init__()

        self.height = self.width = self.DEFAULT_SIZE
        self.maxPlayers = len(self.spawnLocations)

        self.reset()        

    def reset(self):
        super(Classic, self).reset()
        self.field = Field(self.height + 1, self.width + 1, 0, '  ')
        self.p1 = self.field.addPerimeter(self.height, self.width, [0, 0], -1, 's', 31)
        self.obstacles.append(self.p1)

        #Setup spawners
        self.fs1 = frt.FruitSpawner(frt.Plus1Fruit)
        self.fs1.bindAreaToPerimeter(self.p1)
        self.fs1.setMaxFruits(1)
        self.fs1.setFruitRarity(1)

        self.fruitSpawners.append(self.fs1)

        self.spawnLocations = [[1, 1], [3, 3], [5, 5], [7, 7], [9, 5], [11, 3], [13, 1], [18, 18], [11, 9], [7, 13]]
        self.lastNumberOfFruits = [0] * len(self.fruitSpawners)


    def getSpecificColors(self):
        specific_colors = super(Classic, self).getSpecificColors() 
        specific_colors.extend([
            {"number": 31, "fg": "white", "bg": "black"}
        ])
        return specific_colors

    def getSpecificOptions(self):
        opt = super(Classic, self).getSpecificOptions()

        new_opt = {
            "height": self.height,
            "width": self.width
        }

        opt.update(new_opt)

        return opt

    # Maybe do better?
    def setOptions(self, options):
        super(Classic, self).setOptions(options)
        if options.get("height"):
            self.height = self.DEFAULT_SIZE if int(options.get("height")) <= 4 else int(options.get("height"))

        if options.get("width"):
            self.width = self.DEFAULT_SIZE if int(options.get("width")) <= 4 else int(options.get("width"))

        self.field.setDimensions(self.height + 1, self.width + 1)
        self.field.reset()
        self.field.shapes.remove(self.p1)
        self.p1 = self.field.addPerimeter(self.height, self.width, [0, 0], -1, 's', 31)
        self.fs1.bindAreaToPerimeter(self.p1)
        self.field.refresh()

    def update(self):
        super(Classic, self).update()
