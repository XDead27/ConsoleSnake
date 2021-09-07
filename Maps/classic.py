import time
import curses
from Maps.map import Map
from Resources.field import Field
import Resources.fruits as frt


class Classic(Map):
    def __init__(self):
        super(Classic, self).__init__()

        self.DEFAULT_SIZE = 20

        self.field = Field(self.DEFAULT_SIZE + 1, self.DEFAULT_SIZE + 1, 0, '  ')
        self.p1 = self.field.addPerimeter(self.DEFAULT_SIZE, self.DEFAULT_SIZE, [0, 0], -1, 's', 31)
        self.obstacles.append(self.p1)

        #Setup spawners
        self.fs1 = frt.FruitSpawner(frt.Plus1Fruit)
        self.fs1.bindAreaToPerimeter(self.p1)
        self.fs1.setMaxFruits(1)
        self.fs1.setFruitRarity(1)

        self.fruitSpawners.append(self.fs1)

        self.lastNumberOfFruits = [0] * len(self.fruitSpawners)

        self.maxPlayers = 2
        self.spawnLocations = [[1, 1], [3, 3], [5, 5], [7, 7], [9, 5], [11, 3], [13, 1], [18, 18], [11, 9], [7, 13]]

    def getSpecificColors(self):
        specific_colors = super(Classic, self).getSpecificColors() 
        specific_colors.extend([
            {"number": 31, "fg": "white", "bg": "black"}
        ])
        return specific_colors

    # def askForParams(self, stdscr):
    #     super(Classic, self).askForParams(stdscr)
    #     curses.flushinp()
    #     curses.nocbreak()
    #     stdscr.nodelay(False)
    #     stdscr.addstr("Size (height): ")
    #     stdscr.refresh()
    #     h = stdscr.getstr(1, 0, 3).decode("utf-8")
    #     stdscr.addstr("Size (width): ")
    #     w = stdscr.getstr(3, 0, 3).decode("utf-8")

    #     h = self.DEFAULT_SIZE if h == '' else int(h)
    #     w = self.DEFAULT_SIZE if w == '' else int(w)

    #     self.field.setDimensions(h + 1, w + 1)
    #     self.field.reset()
    #     self.field.shapes.remove(self.p1)
    #     self.p1 = self.field.addPerimeter(h, w, [0, 0], -1, 's', 101)
    #     self.fs1.bindAreaToPerimeter(self.p1)
    #     self.field.refresh()

    #     curses.cbreak()
    #     stdscr.nodelay(True)

    def update(self):
        super(Classic, self).update()
