#!/usr/bin/env python3

from art import *
import os
import time
import curses
import argparse as ap
from snek import Snake
from field import Field
import fruits as frt
import importlib
from random import randrange

#Parse flags and arguments
parser = ap.ArgumentParser(description='Snek gaem with frends :>')
parser.add_argument("map", choices=['duel', 'survival', 'classic'], help="Map to play on")
parser.add_argument("--details", action="store_true", help="Display map details and exit")
parser.add_argument("-p", "--players", type=int, default=2, help="Number of players")
parser.add_argument("-f", "--flush-input", action="store_true", help="Makes the game a little harder by not storing inputs after each tick")
parser.add_argument("-r", "--refresh", type=float, default=0.5, required=False, help="Input interval")
parser.add_argument("--manual-inputs", action="store_true", help="Setup inputs manually for each snake")
parser.add_argument("--manual-aesthetics", action="store_true", help="Setup aesthetics manually for each snake")

args = parser.parse_args()

stdscr = curses.initscr()

curses.start_color()
curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_RED)
curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_WHITE)
curses.init_pair(11, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(12, curses.COLOR_GREEN, curses.COLOR_WHITE)

def endCurse():
    curses.nocbreak()
    curses.endwin()

display_font = 'cjk'

m = __import__("Maps." + args.map)
m = getattr(m, args.map)

map = getattr(m, args.map.capitalize())()

if args.details:
    endCurse()
    map.displayDetails(stdscr)
    os._exit(0)

if args.players > map.maxPlayers:
    print("Too many players for this map!")
    endCurse()
    os._exit(0)

def setupName(i):
    stdscr.addstr("\nYour naem sir / ma'am (player " + str(i + 1) +"): ")
    stdscr.refresh()
    x = stdscr.getstr(2, 0, 20)
    x = x.decode("utf-8")
    if x == '':
        return "Player " + str(i+1)
    else:
        return x

def setupControls(name):
    controls = []
    stdscr.addstr("\nSetting up controls for u, " + name + "...")
    stdscr.addstr("\nPwease hit UP key... ")
    controls.append(stdscr.getkey())
    stdscr.addstr("\nNow LEFT... ")
    controls.append(stdscr.getkey())
    stdscr.addstr("\nDOWN even... ")
    controls.append(stdscr.getkey())
    stdscr.addstr("\nRIGHT if I may... ")
    controls.append(stdscr.getkey())
    stdscr.addstr("I very graciously thenk\n\n\n")
    return controls

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

def setupAesthetics(name, i):
    aesthetics = []
    stdscr.addstr("\nNow let's get funkeh with appearance, if you may >//< (for " + name + ")")
    stdscr.addstr("\nSelect character... ")
    curses.noecho()
    x = stdscr.getkey()
    aesthetics.append(x)
    stdscr.addstr(text2art(x, font = display_font))
    curses.echo()
    stdscr.addstr("\nPls the foreground color... ")
    fg = stdscr.getstr().decode("utf-8")
    stdscr.addstr("\nOne more thing. The background if it's not too much to ask... ")
    bg = stdscr.getstr().decode("utf-8")

    curses.init_pair(i+1, parseColor(fg), parseColor(bg))

    aesthetics.append(i+1)
    return aesthetics

#Setup snakes controls and appearance
snakes = []
defaultControls = [['w', 'a', 's', 'd'], ['u', 'h', 'j', 'k']]
defaultAesthetics = [['o', 1], ['o', 2]]
for i in range(args.players):
    controls = None
    aesthetics = None

    name = setupName(i)

    #There is surely a better way to do this
    if args.manual_inputs or len(defaultControls) <= 0:
        controls = setupControls(name)
    else:
        controls = defaultControls[0]
        defaultControls.remove(controls)

    if args.manual_aesthetics or len(defaultAesthetics) <= 0:
        aesthetics = setupAesthetics(name, i)
    else:
        aesthetics = defaultAesthetics[0]
        defaultAesthetics.remove(aesthetics)

    snake = Snake(map.getRandomSpawnLocation(i), 2)
    snake.name = name
    snake.setControls(controls[0], controls[1], controls[2], controls[3])
    snake.setAesthetics(99 + i, aesthetics[0], aesthetics[1])
    snakes.append(snake)
    stdscr.clear()
    stdscr.refresh()

acceptedInputs = []
for s in snakes:
    acceptedInputs.append(s.getControls())

field = map.field
obstacles = map.obstacles
fruitSpawners = map.fruitSpawners
inputs = []
curses.cbreak()
stdscr.nodelay(True)

map.playIntro(stdscr)

map.refreshRate = args.refresh

def getInput(stdscr):
    global inputs
    global snakes
    if args.flush_input:
        curses.flushinp()
    inputs = [None] * len(acceptedInputs)

    usedInputs = acceptedInputs[:]
    #Jesus fucking christ this is so retarded :DDDDDDDD
    time.sleep(map.refreshRate)
    i = 0
    j = 0
    while i < 50 and j < len(snakes):
        i += 1
        a = stdscr.getch()
        if a == -1:
            break
        a = chr(a)
        isOk = False
        for x in range(len(acceptedInputs)):
            if (not a in usedInputs) and (a in acceptedInputs[x]):
                usedInputs.extend(acceptedInputs[x][:])
                inputs[x] = a
                j += 1
                break

def handleInput(s, input):
    boxLeft = s.registerInput(input)

    if not boxLeft == -1:
        field.clearTempNumAt(boxLeft)

    handlePosition(s)

    for x in s.body:
        field.addTempNumAt(x, s.number, s.string, s.color)

def handlePosition(s):
    global fruitSpawner
    global field
    numAtHead = field.getNumAt(s.head)

    if numAtHead == field.blank_number:
        return

    for f in fruitSpawners:
        if isInRange(s.head, f.spawnStart, f.spawnEnd):
            for fruit in f.spawnedFruits:
                if s.head == fruit.start:
                    fruit.doMagic(s, snakes, map)
                    f.spawnedFruits.remove(fruit)
                    field.shapes.remove(fruit)
                    return

    for snake in snakes:
        if s.head == snake.head:
            (s if s.length < snake.length else snake).dead = True
        elif numAtHead == snake.number:
            s.dead = True

    s.dead = True

def drawField(stdscr):
    for x in range(field.height):
        for y in range(field.width):
            stdscr.addstr(text2art(field.drawnMap[x][y][0], font=display_font), curses.color_pair(field.drawnMap[x][y][1]))
        stdscr.addstr('\n')

def displayScore(stdscr):
    stdscr.addstr("\nScore:\n")
    for s in snakes:
        if not s.name:
            stdscr.addstr("Player " + str(snakes.index(s) + 1) + ': ')
        else:
            stdscr.addstr(s.name + ': ')
        stdscr.addstr(str(s.getScore()) + '\n')

def isInRange(pos, start, end):
    return (pos[0] >= start[0] and pos[0] <= end[0] and pos[1] >= start[1] and pos[1] <= end[1])

def doTheDead(s):
    stdscr.clear()
    stdscr.refresh()
    if not s.name:
        tprint("Player " + str(snakes.index(s) + 1), font='unives')
    else:
        tprint(s.name, font='unives')
    tprint("\nis ded :(", font='twisted')
    time.sleep(1)
    curses.flushinp()

#Beware the MAIN
def main(stdscr):
    global inputs
    global field
    global fruitSpawners
    try:
        debugTimerStart = time.time()

        #Big loop
        while True:
            debugTimerEnd = time.time()

            #Clean and draw field thingy
            stdscr.clear()
            drawField(stdscr)
            displayScore(stdscr)
            stdscr.addstr("Loop lag: " + str(debugTimerEnd - debugTimerStart - map.refreshRate))
            stdscr.refresh()

            debugTimerStart = time.time()

            #Get player input
            getInput(stdscr)

            #Handle inputs
            for i in range(len(inputs)):
                if inputs[i] == None:
                    handleInput(snakes[i], snakes[i].direction)
                else:
                    handleInput(snakes[i], inputs[i])

            #Update for map related thingz
            map.update()

            for s in snakes:
                if s.dead:
                    doTheDead(s)
                    stdscr.nodelay(False)
                    stdscr.getch()
                    endCurse()
                    os._exit(0)

    except KeyboardInterrupt:
        endCurse()
        os._exit(0)

curses.wrapper(main)
