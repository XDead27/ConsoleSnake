import time, os, enum
from collections import deque
from numpy import dot
from Resources.snek import Snake
from random import choice, randrange
import Resources.utils as utils

class game_state(enum.Enum):
    NOT_STARTED = 0
    STARTED = 1
    ERROR = -1
    STOPPED = 2

class Game:
    # players & computers
    # ---> array of objects {id (only players), name, aesthetics}    
    # aesthetics
    # ---> object 
    # ---> {char: character,
    #       color_tail: {number, fg, bg},
    #       color_head: {number, fg, bg}
    #      }
    def __init__(self, map, players, computers, flush_input, refresh):
        m = __import__("Maps." + map)
        m = getattr(m, map)

        self.map = getattr(m, map.capitalize())()
        self.colorSettings = []

        # The 'hashmap' 
        self.player_ids = {}

        self.snakes = deque([])

        # Add players
        for i in range(len(players)):
            # Setting the controls is a bit legacy stuff, need to refactor
            # TODO: Get rid of setting controls in online game
            controls = [ord('w'), ord('a'), ord('s'), ord('d')]
            id = players[i].get("id")
            name = players[i].get("name")
            aesthetics = players[i].get("aesthetics")

            snake = Snake(self.map.getRandomSpawnLocation(i), 2)
            snake.name = name
            snake.setControls(controls[0], controls[1], controls[2], controls[3])
            snake.setAesthetics( \
                    99 + i, \
                    aesthetics.get("char"), \
                    aesthetics.get("color_tail").get("number"), \
                    aesthetics.get("color_head").get("number")
                )
            self.colorSettings.append(aesthetics.get("color_tail"))
            self.colorSettings.append(aesthetics.get("color_head"))
            self.snakes.append(snake)

            self.player_ids[id] = snake

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

        self.field = self.map.field
        self.obstacles = self.map.obstacles
        self.fruitSpawners = self.map.fruitSpawners
        self.inputs = []
        self.alive = len(players) + len(computers)

        # For syncronization
        self.last_update_time = time.time()
        self.map.refreshRate = refresh

        # State variables
        self.game_state = game_state.NOT_STARTED


    def getAllColors(self):
        return self.colorSettings

    # Place input (id, input)
    def placeInput(self, id, input):
        pass

    # Handle input
    def handleInput(self, snake, input):
        pass

    # Handle position
    def handlePosition(self, snake):
        pass

    # Update
    def update(self):
        #Sync since last update
        loops_to_perform = int((time.time() - self.last_update_time)/self.map.refreshRate)

        for i in range(loops_to_perform):
            # Get states
            states = []
            for cs in self.comp_snakes:
                states.append(utils.get_state(map, cs))
            
            # Get computer input
            for i in range(len(self.agents)):
                action = self.agents[i].predict_action(states[i])
                self.handleInput(self.comp_snakes[i], utils.positionToKey(action, self.comp_snakes[i]))

            # Handle inputs -- TODO!!!!!
            for i in range(len(self.inputs)):
                if self.inputs[i] == None:
                    self.handleInput(self.snakes[i], self.snakes[i].direction)
                else:
                    self.handleInput(self.snakes[i], self.inputs[i])            

            # Update for map related thingz
            self.map.update()

            ## Implement a better way
            # s_to_remove = [self.snakes[i] for i in range(len(self.snakes)) if self.snakes[i].dead]
            # cs_to_remove = [comp_snakes[i] for i in range(len(comp_snakes)) if comp_snakes[i].dead]
            # for s in s_to_remove:
            #     last_snake = s
            #     doTheDead(s)
            #     alive -= 1
                    
            # for cs in cs_to_remove:
            #     last_snake = cs
            #     doTheDead(cs)
            #     alive -= 1
            
            # alive = len(snakes) + len(comp_snakes)


