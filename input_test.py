import time
import signal
import curses
import os
import art
from field import Field

stdscr = curses.initscr()
curses.cbreak()
curses.start_color()
curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

inputs = []
acceptedInputs = [['w', 'a', 's', 'd'],['u', 'h', 'k', 'j']]

iterNoInput = 0

def noInput(signum, frame):
    global iterNoInput
    iterNoInput += 1
    pass

signal.signal(signal.SIGALRM, noInput)

def main (stdscr):
    global inputs
    global iterNoInput
    iters = 0
    try:
        while True:
            # x = stdscr.getkey()
            # stdscr.addch(art.text2art(x, font='cjk'))
            stdscr.clear()
            stdscr.refresh()
            rows, cols = stdscr.getmaxyx()
            print(str(rows) + " : " + str(cols))
            time.sleep(0.5)
    except KeyboardInterrupt:
        curses.nocbreak()
        curses.endwin()
        os._exit(0)

curses.wrapper(main)
