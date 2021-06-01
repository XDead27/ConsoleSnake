#!/usr/bin/env python3

from art import *
import os
import time
import curses
import math
import argparse as ap
from snek import Snake
from field import Field, distance
import fruits as frt
import importlib
from random import randrange
from NN.deepq import *

#Parse flags and arguments
parser = ap.ArgumentParser(description='Train snaek. Majeek!')
parser.add_argument("map", choices=['duel', 'survival', 'classic'], help="Map to play on")
parser.add_argument("-p", "--players", type=int, default=1, help="Population number")
parser.add_argument("-r", "--refresh", type=float, default=0.0, required=False, help="This should be non zero if you wan see how they move")
parser.add_argument("-g", "--games", type=int, default=0, required=False, help="How many games to run")
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
curses.init_pair(13, curses.COLOR_CYAN, curses.COLOR_WHITE)

def endCurse():
    curses.nocbreak()
    curses.endwin()

display_font = 'cjk'

m = __import__("Maps." + args.map)
m = getattr(m, args.map)

gen = 1
while gen <= args.games or args.games == 0:

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

        snake = Snake([7, 7], 2)
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
    
    h = 15
    w = 15

    map.field.setDimensions(h + 1, w + 1)
    map.field.reset()
    map.field.shapes.remove(map.p1)
    map.p1 = map.field.addPerimeter(h, w, [0, 0], -1, 's', 101)
    map.fs1.bindAreaToPerimeter(map.p1)
    map.field.refresh()

    map.refreshRate = args.refresh

    def handleInput(s, input):
        boxLeft = s.registerInput(input)

        if isinstance(boxLeft, list):
            field.clearTempNumAt(boxLeft)

        handlePosition(s)

        if not s.dead:
            for x in s.body:
                field.addTempNumAt(x, s.number, s.string, s.color)

    def handlePosition(s):
        global fruitSpawner
        global field
        if not (s.head[0] in range(field.height) and s.head[1] in range(field.width)):
            s.dead = True
            return

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

        for o in obstacles:
            if numAtHead == o.number:
                s.dead = True

        
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
        
    def calculate_reward(pos):
        global fruitSpawner
        global field
        if not (pos[0] in range(field.height) and pos[1] in range(field.width)):
            return -1

        numPos = field.getNumAt(pos)
        if numPos == field.blank_number:
            return 0

        for f in fruitSpawners:
            if isInRange(pos, f.spawnStart, f.spawnEnd):
                for fruit in f.spawnedFruits:
                    if pos == fruit.start:
                        return 1

        for o in obstacles:
            if numPos == o.number:
                return -1

        for snake in snakes:
            if numPos == snake.number:
                return -1
    
    def get_state(snake):
        state = field.getProximity(snake, 5, True)
        
        min_distance = np.inf
        closest_fruit = None
        
        for f in fruitSpawners:
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

    #Beware the MAIN
    def main(stdscr):
        global inputs
        global field
        global fruitSpawners
        try:
            debugTimerStart = time.time()
            moves = 0
            games = 0
            
            #TODO: Do thing with dead snakes
            #deadSnakes = []
            
            agent = DQN([122, 90, 90, 70, 4], [leaky_relu, leaky_relu, leaky_relu, linear], [he_init, he_init, he_init, zero_init])

            if os.path.exists("NN/" + args.map + "_dqn.npy"):
                existing_data = np.load("NN/" + args.map + "_dqn.npy", allow_pickle=True)
                games = existing_data[2]
                moves = existing_data[3]
                existing_net = existing_data[0]
                experience = existing_data[1]
                
                agent.init_from_list(np.array(existing_net))
                agent.experience = experience
                
            epsilon = max(40 - games, 3)
            stop = False
                
            #Big loop
            while not snakes[0].dead:
                debugTimerEnd = time.time()
                
                #Clean and draw field thingy
                stdscr.clear()
                drawField(stdscr)
                displayScore(stdscr)
                stdscr.addstr("Loop lag: " + str(debugTimerEnd - debugTimerStart - map.refreshRate))
                stdscr.addstr("\nGame: " + str(games))
                stdscr.addstr("\nMove: " + str(moves) + "\n")
                stdscr.addstr("\nMean error: " + str(agent.mean_error) + "\n")                
                if stop: 
                    stdscr.addstr("\nMB surprise sm: " + str([agent.last_minibatch[i][2] for i in range(len(agent.last_minibatch))]) + "\n")   
                    stdscr.addstr("\nMax surprise: " + str(np.max([agent.experience[i][5] for i in range(len(agent.experience))])) + "\n")   
                    stop = False   
                    stdscr.refresh()        
                    time.sleep(5)  
                stdscr.refresh()

                debugTimerStart = time.time()

                #Get AI output
                #Get proximity
                state = get_state(snakes[0])

                if epsilon > randint(1, 30):
                    action = choice([0, 1, 2, 3])
                else:
                    #print(state)
                    action = agent.predict_action(state)
                reward = calculate_reward(snakes[0].calculateNextPose(positionToKey(action, snakes[0])))
                
                #Handle inputs
                handleInput(snakes[0], positionToKey(action, snakes[0]))
                #Update for map related thingz
                map.update()
                
                new_state = get_state(snakes[0])
                dead = snakes[0].dead
                
                agent.store_experience(state, action, reward, new_state, dead)
                moves += 1
                
                if(moves % 16 == 0):
                    agent.train()
                    stop=True
                    
                if(moves % 120 == 0):
                    agent.update_target_model()

                time.sleep(args.refresh)

            #Save the net
            games += 1
            data = np.array([agent.main_model.nn, agent.experience, games, moves])
            np.save("NN/" + args.map + "_dqn.npy", data)
            time.sleep(2 * args.refresh)


        except KeyboardInterrupt:
            endCurse()
            os._exit(0)

    curses.wrapper(main)
    gen += 1
