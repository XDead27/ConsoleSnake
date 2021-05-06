import math
import inspect

class Segment:
    def __init__(self, start, end, number, string, color):
        self.start = start
        self.end = end
        self.number = number
        self.string = string
        self.color = color

    def getLength(self):
        return math.sqrt((self.start[0] - self.end[0]) ** 2 + (self.start[1] - self.end[1]) ** 2)

class Perimeter:
    def __init__(self, height, width, pos, number, string, color):
        self.width = width
        self.height = height
        self.number = number
        self.string = string
        self.position = pos
        self.color = color


class Field:
    shapes = []

    def __init__(self, height, width, blank_number = 0, blank_string = '  '):
        self.setDimensions(height, width)
        self.blank_number = blank_number
        self.blank_string = blank_string
        self.reset()
        self.shapes = []

    def setBlankString(self, string):
        self.blank_string = string
        self.refresh()

    def setDimensions(self, height, width):
        self.width = width
        self.height = height

    def drawSegment(self, seg):
        if seg.end[1] - seg.start[1] == 0:
            for x in range(seg.start[0], seg.end[0] + 1):
                self.map[x][seg.start[1]] = seg.number
                self.drawnMap[x][seg.start[1]] = [seg.string, seg.color]
        else:
            slope = (seg.end[0] - seg.start[0])/(seg.end[1] - seg.start[1])
            for x in range(min(seg.start[0], seg.end[0]), max(seg.start[0], seg.end[0]) + 1):
                for y in range(min(seg.start[1], seg.end[1]), max(seg.start[1], seg.end[1]) + 1):
                    #Maybe fix ?? dunno math
                    ord = (x - seg.start[0]) / (slope if abs(slope) > 1 else 1)
                    absc = (slope if abs(slope) <= 1 else 1) * (y - seg.start[1])
                    if math.floor(ord) == math.floor(absc):
                        self.map[x][y] = seg.number
                        self.drawnMap[x][y] = [seg.string, seg.color]

    def drawPerimeter(self, per):
        for x in range(per.height):
            if x == 0 or x == per.height - 1:
                for y in range(per.width):
                    self.map[per.position[0] + x][per.position[1] + y] = per.number
                    self.drawnMap[per.position[0] + x][per.position[1] + y] = [per.string, per.color]
            else:
                self.map[per.position[0] + x][per.position[1]] = per.number
                self.drawnMap[per.position[0] + x][per.position[1]] = [per.string, per.color]
                self.map[per.position[0] + x][per.position[1] + per.width - 1] = per.number
                self.drawnMap[per.position[0] + x][per.position[1] + per.width - 1] = [per.string, per.color]

    def resizePerimeter(self, per, newHeight, newWidth):
        ##I should never be allowed to write code again :>
        #Here we just MAKE A NEW PERIMETER so it covers the last one
        #thus erasing its trace :)
        tempPer = self.addPerimeter(per.height, per.width, per.position, self.blank_number, self.blank_string, 100)
        self.shapes.remove(tempPer)
        #Then we redraw the last one in the right place
        per.height = newHeight
        per.width = newWidth
        self.drawPerimeter(per)

    def appendSegment(self, segment):
        if not (segment.start[0] in range(self.height) or segment.start[1] in range(self.width) or segment.end[0] in range(self.height) or segment.end[1] in range(self.width)):
            return -1

        self.shapes.append(segment)

        self.drawSegment(segment)

        return segment

    def addSegment(self, start, end, number, string, color):
        if not (start[0] in range(self.height) or start[1] in range(self.width) or end[0] in range(self.height) or end[1] in range(self.width)):
            return -1

        newSegment = Segment(start, end, number, string, color)
        self.shapes.append(newSegment)

        self.drawSegment(newSegment)

        #WHY THE FUCK DID I NEED A TUPLE????
        ## TODO: remove tuple
        return newSegment


    def addPerimeter(self, height, width, position, number, string, color):
        endHeight = height + position[0]
        endWidth = width + position[1]
        if endHeight > self.height or endWidth > self.width:
            return -1

        newPerimeter = Perimeter(height, width, position, number, string, color)
        self.shapes.append(newPerimeter)

        self.drawPerimeter(newPerimeter)

        return newPerimeter

    def deleteShape(self, shape):
        for x in self.shapes:
            if x[0] == shape:
                del x

    def clearTempNumAt(self, position):
        self.addTempNumAt(position, self.blank_number, self.blank_string, 100)

    def addTempNumAt(self,position, num, char, color):
        self.map[position[0]][position[1]] = num
        self.drawnMap[position[0]][position[1]] = [char, color]

    def addNumAt(self, position, num, char, color):
        return self.addSegment(position, position, num, char, color)

    def getNumAt(self, position):
        return self.map[position[0]][position[1]]

    def getProximity(self, snake, radius, showTemps = False):
        position = snake.head
        startH = position[0] - radius
        startW = position[1] - radius
        endH = position[0] + radius
        endW = position[1] + radius

        proximity = []

        for x in range(startH, endH + 1):
            for y in range(startW, endW + 1):
                if not x in range(self.height) or not y in range(self.width):
                    proximity.append(0)
                elif self.map[x][y] == snake.number:
                    proximity.append(99)
                elif not showTemps and self.map[x][y] >= 99:
                    proximity.append(0)
                else:
                    proximity.append(self.map[x][y])

        return proximity

    def refreshDrawnMap(self, additional = []):
        for x in range(self.height):
            for y in range(self.width):
                if self.map[x][y] == self.blank_number:
                    self.drawnMap[x][y] = [self.blank_string, 0]
                for p in self.shapes:
                    if self.map[x][y] == p.number:
                        self.drawnMap[x][y] = [p.string, p.color]
                for a in additional:
                    if self.map[x][y] == a[0]:
                        self.drawnMap[x][y] = [a[1][0], a[1][1]]

        return self.drawnMap

    def reset(self):
        self.map = [[self.blank_number for x in range(self.width)] for y in range(self.height)]
        self.drawnMap = [[[self.blank_string, 0] for x in range(self.width)] for y in range(self.height)]

    def refresh(self):
        self.reset()

        for s in self.shapes:
            if isinstance(s, Segment):
                self.drawSegment(s)
            else:
                self.drawPerimeter(s)

        self.refreshDrawnMap()
