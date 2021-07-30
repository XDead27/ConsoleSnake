#!/usr/bin/env python3

from art import text2art, tprint
import curses, time, os
from collections import deque
import argparse as ap
from numpy import dot
from Resources.snek import Snake
from random import choice, randrange
from Maps.map import playIntro, displayDetails
import Resources.utils as utils

#Parse flags and arguments
parser = ap.ArgumentParser(description='Snek gaem with frends :>')
parser.add_argument("map", choices=['duel', 'survival', 'classic', 'dungeons'], help="Map to play on")
parser.add_argument("--details", action="store_true", help="Display map details and exit")
parser.add_argument("-p", "--players", type=int, default=2, help="Number of players")
parser.add_argument("-c", "--computers", type=int, default=0, help="Number of computers")
parser.add_argument("-f", "--flush-input", action="store_true", help="Makes the game a little harder by not storing inputs after each tick")
parser.add_argument("-r", "--refresh", type=float, default=0.5, required=False, help="Input interval")
parser.add_argument("--manual-inputs", action="store_true", help="Setup inputs manually for each snake")
parser.add_argument("--manual-aesthetics", action="store_true", help="Setup aesthetics manually for each snake")

args = parser.parse_args()

if args.computers > 0:
    from NN.deepq import DQN, leaky_relu, linear, he_init, zero_init

stdscr = curses.initscr()

curses.start_color()
curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(201, curses.COLOR_GREEN, curses.COLOR_GREEN)
curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(202, curses.COLOR_RED, curses.COLOR_RED)
curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_RED)
curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_WHITE)
curses.init_pair(11, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(12, curses.COLOR_GREEN, curses.COLOR_WHITE)
curses.init_pair(13, curses.COLOR_CYAN, curses.COLOR_WHITE)

def endCurse():
    curses.nocbreak()
    curses.endwin()

display_font = 'cjk'

m = __import__("Maps." + args.map)
m = getattr(m, args.map)

map = getattr(m, args.map.capitalize())()

for color in map.getSpecificColors():
    curses.init_pair(color['number'], utils.parseColor(color['fg']), utils.parseColor(color['bg']))

if args.details:
    endCurse()
    details = map.getDetails()
    displayDetails(details)
    os._exit(0)

if args.players + args.computers > map.maxPlayers:
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
    controls.append(stdscr.getch())
    stdscr.addstr("\nNow LEFT... ")
    controls.append(stdscr.getch())
    stdscr.addstr("\nDOWN even... ")
    controls.append(stdscr.getch())
    stdscr.addstr("\nRIGHT if I may... ")
    controls.append(stdscr.getch())
    stdscr.addstr("\nI very graciously thenk\n\n\n")
    stdscr.refresh()
    time.sleep(1)
    return controls

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

    curses.init_pair(i+1, utils.parseColor(fg), utils.parseColor(bg))
    curses.init_pair(200 + i + 1, utils.parseColor(fg), utils.parseColor(fg))

    aesthetics.append(i+1)
    aesthetics.append(200 + i + 1)
    return aesthetics

#Setup snakes controls and appearance
snakes = deque([])
defaultControls = [[ord('w'), ord('a'), ord('s'), ord('d')], [ord('u'), ord('h'), ord('j'), ord('k')]]
defaultAesthetics = [['o', 1, 201], ['o', 2, 202]]
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
    snake.setAesthetics(99 + i, aesthetics[0], aesthetics[1], aesthetics[2])
    snakes.append(snake)
    stdscr.clear()
    stdscr.refresh()

acceptedInputs = []
for s in snakes:
    acceptedInputs.append(s.getControls())
    
#Setup computer snakes
comp_snakes = deque([])
agents = deque([])
for i in range(args.computers):
    name = "Hank " + str(i+1)
    snake = Snake(map.getRandomSpawnLocation(-(i+1)), 2)
    snake.name = name
    snake.setControls(1, 2, 3, 4)
    
    #random aesthetics -- yes it is indeed a mess
    fg, bg = choice(['green', 'white', 'black', 'magenta', 'cyan']), choice(['green', 'white', 'black', 'magenta', 'cyan'])
    curses.init_pair(map.maxPlayers - i + 1, utils.parseColor(fg), utils.parseColor(bg))
    curses.init_pair(200 + map.maxPlayers - i + 1, utils.parseColor(fg), utils.parseColor(fg))
    snake.setAesthetics(99 + map.maxPlayers - i, choice(['o', 'h', 'b', 'l', 'd']), map.maxPlayers - i + 1, 200 + map.maxPlayers - i + 1)
    comp_snakes.append(snake)
    stdscr.clear()
    stdscr.refresh()
    
    agent = DQN([122, 90, 90, 70, 4], [leaky_relu, leaky_relu, leaky_relu, linear], [he_init, he_init, he_init, zero_init])
    agent.load_from_file("NN/" + args.map + "_dqn_v1.1.npy")
    agents.append(agent)

field = map.field
obstacles = map.obstacles
fruitSpawners = map.fruitSpawners
inputs = []
curses.cbreak()
stdscr.nodelay(True)

playIntro(args.map)

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

    if not s.dead:
        for x in s.body:
            if x == s.head:
                field.addTempNumAt(x, s.number, s.string, s.head_color)
            else:
                field.addTempNumAt(x, s.number, s.string, s.color)
    else:
        for x in s.body:
            if not x == s.head: field.clearTempNumAt(x)

def handlePosition(s):
    global field
    numAtHead = field.getNumAt(s.head)

    if numAtHead == field.blank_number:
        return

    for f in fruitSpawners:
        if utils.isInRange(s.head, f.spawnStart, f.spawnEnd):
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
    
    for s in comp_snakes:
        if not s.name:
            stdscr.addstr("Computer " + str(comp_snakes.index(s) + 1) + ': ')
        else:
            stdscr.addstr(s.name + ': ')
        stdscr.addstr(str(s.getScore()) + '\n')

def doTheDead(s):
    if s in snakes:
        #if s is a player, remove its inputs and then remove it from the list
        idx = snakes.index(s)
        del acceptedInputs[idx]
        snakes.remove(s)
    elif s in comp_snakes:
        #if s is a computer, remove its agent and then remove it from the list
        idx = comp_snakes.index(s)
        del agents[idx]
        comp_snakes.remove(s)
    
def doTheWin(s):
    stdscr.clear()
    stdscr.refresh()
    if not s.name:
        tprint("Player " + str(snakes.index(s) + 1), font='unives')
    else:
        tprint(s.name, font='unives')
    tprint("\nwon :>", font='twisted')
    time.sleep(1)
    curses.flushinp()

#Beware the MAIN
def main(stdscr):
    global inputs
    global field
    global fruitSpawners
    try:
        debugTimerStart = time.time()
        alive = args.players + args.computers
        last_snake = None

        #Big loop
        while alive >= 1:
            debugTimerEnd = time.time()

            #Clean and draw field thingy
            stdscr.clear()
            drawField(stdscr)
            displayScore(stdscr)
            stdscr.addstr("Loop lag: " + str(debugTimerEnd - debugTimerStart - map.refreshRate))
            stdscr.refresh()

            debugTimerStart = time.time()
            
            #Get states
            states = []
            for cs in comp_snakes:
                states.append(utils.get_state(map, cs))
            
            #Get computer input
            for i in range(len(agents)):
                action = agents[i].predict_action(states[i])
                handleInput(comp_snakes[i], utils.positionToKey(action, comp_snakes[i]))

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

            s_to_remove = [snakes[i] for i in range(len(snakes)) if snakes[i].dead]
            cs_to_remove = [comp_snakes[i] for i in range(len(comp_snakes)) if comp_snakes[i].dead]
            for s in s_to_remove:
                last_snake = s
                doTheDead(s)
                alive -= 1
                    
            for cs in cs_to_remove:
                last_snake = cs
                doTheDead(cs)
                alive -= 1
            
            # alive = len(snakes) + len(comp_snakes)
              
        doTheWin(last_snake)
        stdscr.nodelay(False)
        stdscr.getch()
        endCurse()
        os._exit(0)
        
    except KeyboardInterrupt:
        endCurse()
        os._exit(0)

curses.wrapper(main)
