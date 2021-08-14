import collections
import curses, enum

class Direction(enum.IntEnum):
    UP = 119
    DOWN = 115
    LEFT = 97
    RIGHT = 100

class Snake:
    def __init__ (self, startPos = [1, 1], startLength = 2):
        self.head = startPos
        self.length = startLength
        self.body = collections.deque([self.head])
        self.setControls('w', 'a', 's', 'd')
        self.dead = False
        self.name = ''
        self.additionalScore = 0
        self.moves_from_last_fruit = 0

    def getScore(self):
        return self.additionalScore + 50 * self.length

    def setName(self, name):
        self.name = name

    def setControls(self, up, left, down, right):
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.direction = self.right

    def getControls(self):
        return [self.up, self.down, self.left, self.right]

    def setAesthetics(self, number, string, color, head_color = None):
        self.number = number
        self.string = string
        self.color = color
        self.head_color = head_color

    # This function gets an input, updates the head coordinate and returns the coordinates of the box that has been freed
    # If the snake grew, then this function returns -1
    def registerInput(self, input):
        if(input == self.up or input == self.right or input == self.left or input == self.down):
            if (input == self.up and not self.direction == self.down) or (input == self.right and not self.direction == self.left) or (input == self.down and not self.direction == self.up) or (input == self.left and not self.direction == self.right):
                self.direction = input

            if self.direction == self.up:
                self.head[0] += -1
            elif self.direction == self.right:
                self.head[1] += 1
            elif self.direction == self.down:
                self.head[0] += 1
            elif self.direction == self.left:
                self.head[1] += -1

            self.body.append(self.head[:])

            if(len(self.body) > self.length):
                to_del = self.body.popleft()
                return to_del
            else:
                return -1
            
    def calculateNextPose(self, input):
        if(input == self.up or input == self.right or input == self.left or input == self.down):
            if (input == self.up and not self.direction == self.down) or (input == self.right and not self.direction == self.left) or (input == self.down and not self.direction == self.up) or (input == self.left and not self.direction == self.right):
                dir = input
            else:
                dir = self.direction
                
            curr_head = self.head[:]

            if dir == self.up:
                curr_head[0] += -1
            elif dir == self.right:
                curr_head[1] += 1
            elif dir == self.down:
                curr_head[0] += 1
            elif dir == self.left:
                curr_head[1] += -1

            return curr_head
