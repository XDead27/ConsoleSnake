import math
import curses

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