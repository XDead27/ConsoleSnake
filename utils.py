import curses
import numpy as np
from field import distance

def parseColor(color):
    color = color.lower()
    if color == "black":
        return curses.COLOR_BLACK
    elif color == "white":
        return curses.COLOR_WHITE
    elif color == "red":
        return curses.COLOR_RED
    elif color == "blue":
        return curses.COLOR_BLUE
    elif color == "green":
        return curses.COLOR_GREEN
    elif color == "magenta":
        return curses.COLOR_MAGENTA
    elif color == "cyan":
        return curses.COLOR_CYAN
    elif color == "yellow":
        return curses.COLOR_YELLOW
    else:
        return curses.COLOR_WHITE
    

def isInRange(pos, start, end):
    return (pos[0] >= start[0] and pos[0] <= end[0] and pos[1] >= start[1] and pos[1] <= end[1])

def positionToKey(pos, snake):
        if pos == 0:
            return snake.up
        elif pos == 1:
            return snake.left
        elif pos == 2:
            return snake.down
        elif pos == 3:
            return snake.right
        
def get_state(map, snake):
        state = map.field.getProximity(snake, 5, True)
        
        min_distance = np.inf
        closest_fruit = None
        
        for f in map.fruitSpawners:
            if isInRange(snake.head, f.spawnStart, f.spawnEnd):
                for fruit in f.spawnedFruits:
                    if min_distance > distance(snake.head, fruit.start):
                        min_distance = distance(snake.head, fruit.start)
                        closest_fruit = fruit
        
        if closest_fruit == None:
            fruit_sine = 2
        else:
            fruit_sine = (closest_fruit.start[0] - snake.head[0]) / max(min_distance, 0.1)
        
        state.append(fruit_sine)
        return state
    
def print_state(stdscr, snake):
    state = get_state(snake)
    
    stdscr.addstr("\nSnake vision:\n")
    
    for i in range(11):
        for j in range(11):
            stdscr.addstr(str(state[i*11 + j]))
            #stdscr.addstr(str(len(state)))
        stdscr.addstr('\n')
    stdscr.addstr(str(state[-1]))
