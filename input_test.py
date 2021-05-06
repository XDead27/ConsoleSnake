import time
import signal
import curses
import os
from field import Field

stdscr = curses.initscr()
curses.cbreak()
stdscr.nodelay(True)
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
            curses.flushinp()
            stdscr.clear()
            stdscr.refresh()

            print("Start loop: " + str(iters) + "\n")

            time.sleep(1)
            inputs = [None] * len(acceptedInputs)
            usedInputs = []
            i = 0
            j = 0
            while i < 50 and j < 2:
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

            to_print = ''

            for x in inputs:
                to_print += str(x) + ", "

            print(to_print)
            time.sleep(2)
            iters += 1

        stdscr.getch()
        curses.nocbreak()
        curses.endwin()
        os._exit(0)
    except KeyboardInterrupt:
        curses.nocbreak()
        curses.endwin()
        os._exit(0)

curses.wrapper(main)
