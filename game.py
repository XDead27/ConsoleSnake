import time, os, enum, threading
from collections import deque
from numpy import dot
from Resources.snek import Snake
from random import choice, randrange
from Resources.snek import Direction
import Resources.utils as utils

class GameState(enum.IntEnum):
    NOT_STARTED = 0
    STARTED = 1
    ERROR = -1
    STOPPED = 2

def int_to_string(integer):
    if integer == GameState.NOT_STARTED:
        return "not started"
    elif integer == GameState.STARTED:
        return "started"
    elif integer == GameState.ERROR:
        return "error"
    elif integer == GameState.STOPPED:
        return "stopped"

class Game(threading.Thread):
    # players & computers
    # ---> array of objects {id (only players), name, aesthetics}    
    # aesthetics
    # ---> object 
    # ---> {char: character,
    #       color_tail: {fg, bg},
    #       color_head: {fg, bg}
    #      }
    def __init__(self, game_id, map, players, computers, flush_input, refresh):
        threading.Thread.__init__(self)

        self.game_id = game_id

        self.game_state = GameState.NOT_STARTED

        m = __import__("Maps." + map)
        m = getattr(m, map)

        self.map = getattr(m, map.capitalize())()
        self.colorSettings = []

        # The 'hashmap' 
        self.player_snakes = {}

        # Add players
        for i in range(len(players)):
            id = players[i].get("id")
            name = players[i].get("name")
            aesthetics = players[i].get("aesthetics")

            snake = Snake(self.map.getRandomSpawnLocation(i), 2)
            snake.name = name

            # Setting the controls is a bit legacy stuff, need to refactor
            # TODO: Get rid of setting controls in online game
            snake.setControls(Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT)

            # Find free color numbers
            aesthetics["color_tail"]["number"] = 50 + i
            aesthetics["color_head"]["number"] = 100 + i

            snake.setAesthetics( \
                    99 + i, \
                    aesthetics.get("char"), \
                    aesthetics.get("color_tail").get("number"), \
                    aesthetics.get("color_head").get("number")
                )
            self.colorSettings.append(aesthetics.get("color_tail"))
            self.colorSettings.append(aesthetics.get("color_head"))
            # self.snakes.append(snake)

            self.player_snakes[id] = snake

        self.comp_snakes = deque([])
        self.agents = deque([])

        if len(computers) > 0:
            from NN.deepq import DQN, leaky_relu, linear, he_init, zero_init 

            # Add computers
            for i in range(len(computers)):
                name = "Hank " + str(i+1)
                snake = Snake(self.map.getRandomSpawnLocation(-(i+1)), 2)
                snake.name = name
                snake.setControls(1, 2, 3, 4)
                
                #random aesthetics -- yes it is indeed a mess
                fg, bg = choice(['green', 'white', 'black', 'magenta', 'cyan']), choice(['green', 'white', 'black', 'magenta', 'cyan'])
                self.colorSettings.append({
                        "number": self.map.maxPlayers - i + 1,
                        "fg": fg,
                        "bg": bg
                    })

                self.colorSettings.append({
                        "number": 200 + self.map.maxPlayers - i + 1,
                        "fg": fg,
                        "bg": fg
                    })
                snake.setAesthetics(99 + map.maxPlayers - i, choice(['o', 'h', 'b', 'l', 'd']), map.maxPlayers - i + 1, 200 + map.maxPlayers - i + 1)
                self.comp_snakes.append(snake)
                
                agent = DQN([122, 90, 90, 70, 4], [leaky_relu, leaky_relu, leaky_relu, linear], [he_init, he_init, he_init, zero_init])
                agent.load_from_file("NN/" + map + "_dqn_v1.1.npy")
                self.agents.append(agent)

        self.game_winner = None

        # Get map variables and store them locally
        self.field = self.map.field
        self.obstacles = self.map.obstacles
        self.fruitSpawners = self.map.fruitSpawners
        self.colorSettings.extend(self.map.getSpecificColors())

        # Initialize all inputs to RIGHT
        self.inputs = {}
        for id in self.player_snakes.keys():
            self.inputs[id] = Direction.RIGHT

        self.alive = len(players) + len(computers)

        # For syncronization
        self.last_update_time = time.time()
        self.map.refreshRate = refresh

        # State variables
        self.game_state = GameState.STARTED


    def getAllColors(self):
        return self.colorSettings

    def getScores(self):
        scores = []

        for snake in self.player_snakes.values():
            this_score = {
                "name": snake.name,
                "score": snake.getScore()
            }
            scores.append(this_score)

        for snake in self.comp_snakes:
            this_score = {
                "name": snake.name,
                "score": snake.getScore()
            }
            scores.append(this_score)

        return scores

        

    # Place input (player_id, input)
    def placeInput(self, player_id, input):
        self.inputs[player_id] = input
        pass

    # Handle input
    def handleInput(self, snake, input):
        boxLeft = snake.registerInput(input)

        if not boxLeft == -1:
            self.field.clearTempNumAt(boxLeft)

        self.handlePosition(snake)

        if not snake.dead:
            for x in snake.body:
                if x == snake.head:
                    self.field.addTempNumAt(x, snake.number, snake.string, snake.head_color)
                else:
                    self.field.addTempNumAt(x, snake.number, snake.string, snake.color)
        else:
            for x in snake.body:
                if not x == snake.head: self.field.clearTempNumAt(x)

    # Handle position
    def handlePosition(self, snake):
        numAtHead = self.field.getNumAt(snake.head)

        if numAtHead == self.field.blank_number:
            return

        for f in self.fruitSpawners:
            if utils.isInRange(snake.head, f.spawnStart, f.spawnEnd):
                for fruit in f.spawnedFruits:
                    if snake.head == fruit.start:
                        fruit.doMagic(snake, self.player_snakes.values(), self.map)
                        f.spawnedFruits.remove(fruit)
                        self.field.shapes.remove(fruit)
                        return

        for s in self.player_snakes.values():
            if not s == snake:
                if s.head == snake.head:
                    (s if s.length < snake.length else snake).dead = True
                elif numAtHead == s.number:
                    snake.dead = True

        snake.dead = True

    # Update
    def update(self):
        # Sync since last update
        probing_time = time.time()
        loops_to_perform = int((probing_time - self.last_update_time) / self.map.refreshRate)

        for i in range(loops_to_perform):
            # Get states
            states = []
            for cs in self.comp_snakes:
                states.append(utils.get_state(map, cs))
            
            # Get computer input
            for i in range(len(self.agents)):
                action = self.agents[i].predict_action(states[i])
                self.handleInput(self.comp_snakes[i], utils.positionToKey(action, self.comp_snakes[i]))

            # Handle inputs
            for id in self.player_snakes.keys():
                self.handleInput(self.player_snakes[id], self.inputs[id])            

            # Update for map related thingz
            self.map.update()

            # Check for dead snakes -- maybe move to handle position?
            temp_ids = self.player_snakes.copy().keys()
            for id in temp_ids:
                if self.player_snakes[id].dead:
                    self.alive -= 1

                    #print("Popped - " + self.player_snakes.pop(id, None).name)

                    if self.alive <= 0:
                        self.game_state = GameState.STOPPED
                        self.game_winner = self.player_snakes.pop(id, None).name
                        break

                    self.player_snakes.pop(id, None)

            self.last_update_time = time.time()

            ## TODO: Make computers die

    def run(self):
        while not self.game_state == GameState.STOPPED:
            self.update()
            # Do not waste cpu cycles
            time.sleep(0.01)
