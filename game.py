from art import text2art, tprint
import curses, time, os
from collections import deque
from numpy import dot
from Resources.snek import Snake
from random import choice, randrange
import Resources.utils as utils

class Game:
    # players & computers
    # ---> array of objects {name, aesthetics}    
    def __init__(self, map, players, computers, flush_input, refresh):



        self.display_font = 'cjk'

        m = __import__("Maps." + map)
        m = getattr(m, map)

        self.map = getattr(m, map.capitalize())()