#!/usr/bin/env python3

from art import *
import os
import time
import curses
import math
import argparse as ap
from snek import Snake
from field import Field
import fruits as frt
import importlib
from random import randrange
from NN import ga, nn

#Parse flags and arguments
parser = ap.ArgumentParser(description='Train snaek. Majeek!')
parser.add_argument("map", choices=['duel', 'survival', 'classic'], help="Map to play on")
parser.add_argument("-p", "--players", type=int, default=2, help="Population number")
parser.add_argument("-r", "--refresh", type=float, default=0.0, required=False, help="This should be non zero if you wan see how they move")
parser.add_argument("-g", "--generations", type=int, default=0, required=False, help="How many generations to run")
parser.add_argument("--manual-inputs", action="store_true", help="Setup inputs manually for each snake")
parser.add_argument("--manual-aesthetics", action="store_true", help="Setup aesthetics manually for each snake")
parser.add_argument("--collision", action="store_true", help="Do they bump into eachother?")
parser.add_argument("--max-moves", type=int, default=200, required=False, help="How many times are they allowed to run in circles?")

args = parser.parse_args()

stdscr = curses.initscr()

curses.start_color()

def endCurse():
    curses.nocbreak()
    curses.endwin()

display_font = 'cjk'

m = __import__("Maps." + args.map)
m = getattr(m, args.map)

gen = 1
while gen <= args.generations or args.generations == 0:

    map = getattr(m, args.map.capitalize())()

    def setupName(i):
        return "Player " + str(i+1)

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

    def setupAesthetics(name):
        aesthetics = []
        stdscr.addstr("\nNow let's get funkeh with appearance, if you may >//< (for " + name + ")")
        stdscr.addstr("\nSelect string... ")
        curses.noecho()
        x = stdscr.getkey()
        aesthetics.append(x)
        stdscr.addstr(text2art(x, font = display_font))
        curses.echo()
        stdscr.addstr("\nNow the color... ")
        aesthetics.append(int(stdscr.getkey()))
        return aesthetics

    #Setup snakes controls and appearance
    snakes = []
    defaultControls = ['w', 'a', 's', 'd']
    defaultAesthetics = ['o', 1]
    for i in range(args.players):
        controls = None
        aesthetics = None

        name = setupName(i)

        #There is surely a better way to do this
        if args.manual_inputs or len(defaultControls) <= 0:
            controls = setupControls(name)
        else:
            controls = defaultControls

        if args.manual_aesthetics or len(defaultAesthetics) <= 0:
            aesthetics = setupAesthetics(name)
        else:
            aesthetics = defaultAesthetics

        snake = Snake(map.getRandomSpawnLocation(i), 2)
        snake.name = name
        snake.setControls(controls[0], controls[1], controls[2], controls[3])
        snake.setAesthetics(99 + i, aesthetics[0], aesthetics[1])
        snakes.append(snake)
        stdscr.clear()
        stdscr.refresh()

    field = map.field
    obstacles = map.obstacles
    fruitSpawners = map.fruitSpawners
    inputs = []

    map.refreshRate = args.refresh

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
                        fruit.doMagic(s, field)
                        f.spawnedFruits.remove(fruit)
                        field.shapes.remove(fruit)
                        return

        for o in obstacles:
            if numAtHead == o.number:
                s.dead = True

        if args.collision:
            for snake in snakes:
                if s.head == snake.head:
                    (s if s.length < snake.length else snake).dead = True
                elif numAtHead == snake.number:
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

    def positionToKey(pos, snake):
        if pos == 0:
            return snake.up
        elif pos == 1:
            return snake.left
        elif pos == 2:
            return snake.down
        elif pos == 3:
            return snake.right

    def takeSecond(elem):
        return elem[1]

    #Beware the MAIN
    def main(stdscr):
        global inputs
        global field
        global fruitSpawners
        try:
            debugTimerStart = time.time()
            pop = []
            lastWinners = []
            popDead = 0
            deadSnakes = []
            moves = 0
            rankings = []

            if os.path.exists("NN/" + args.map + ".save"):
                lastWinners = nn.restore("NN/" + args.map + ".save")
                for x in lastWinners:
                    winner = nn.ANN(1, [1], 1)
                    winner.init_network_from_list(x)
                    pop.append(winner)

            for i in range(args.players - len(lastWinners)):
                pop.append(nn.ANN(121, [100, 100], 4))

            #Big loop
            while not popDead == args.players and moves < args.max_moves:
                debugTimerEnd = time.time()

                #Clean and draw field thingy
                stdscr.clear()
                drawField(stdscr)
                displayScore(stdscr)
                stdscr.addstr("Loop lag: " + str(debugTimerEnd - debugTimerStart - map.refreshRate))
                stdscr.addstr("\nGeneration: " + str(gen))
                stdscr.refresh()

                debugTimerStart = time.time()

                #Get AI output
                inputs = []
                for x in range(len(snakes)):
                    if not snakes[x] in deadSnakes:
                        #Get proximity
                        gannInputs = field.getProximity(snakes[x], 5, args.collision)

                        outputAsKey = positionToKey(pop[x].get_highest_output(gannInputs), snakes[x])
                        #Handle inputs
                        handleInput(snakes[x], outputAsKey)

                #Update for map related thingz
                map.update()

                for x in range(len(snakes)):
                    if not snakes[x] in deadSnakes:
                        snakes[x].additionalScore += 0.5
                        if snakes[x].dead:
                            rankings.append([pop[x], snakes[x].getScore()])
                            deadSnakes.append(snakes[x])
                            popDead += 1
                            field.refresh()

                moves += 1
                time.sleep(args.refresh)

            #Sort rankings by snake score
            rankings.sort(key=takeSecond)

            #Save the best n (20% of pop) in a separate file
            n = math.floor(0.2 * args.players) if math.floor(0.2 * args.players) > 2 else 2
            n = (n + 1) if n%2 == 1 else n
            theQuirkiest = []
            for winner in rankings[-n:]:
                theQuirkiest.append(winner[0].nn)

            children = []
            i = 0
            while i < len(theQuirkiest):
                children.extend(ga.breedTwo(theQuirkiest[i], theQuirkiest[i+1]))
                i += 2

            nn.store(children, "NN/" + args.map + ".save")
            time.sleep(2 * args.refresh)


        except KeyboardInterrupt:
            endCurse()
            os._exit(0)

    curses.wrapper(main)
    gen += 1
