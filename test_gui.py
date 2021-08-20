#!/usr/bin/env python

import curses, time, sys
import Resources.utils as utils
import Resources.menu as menu
from test_client import GameClient, InputThread
from game import GameState
from art import text2art

def drawField(stdscr, drawn_map, curses_color):
    for x in range(len(drawn_map)):
        for y in range(len(drawn_map[x])):
            if curses_color:
                stdscr.addstr(text2art(drawn_map[x][y][0], font='cjk'), curses.color_pair(drawn_map[x][y][1]))
            else:
                stdscr.addstr(text2art(drawn_map[x][y][0], font='cjk'))
        stdscr.addstr('\n')

class MyApp(object):
    def __init__(self, stdscreen):
        self.screen = stdscreen
        curses.curs_set(0)

        submenu_items = [("start", self.play_game), ("flash", curses.flash)]
        submenu = menu.Menu(submenu_items, self.screen)

        main_menu_items = [
            ("beep", curses.beep),
            ("flash", curses.flash),
            ("submenu", submenu.display),
        ]
        main_menu = menu.Menu(main_menu_items, self.screen)
        main_menu.display()

    def play_game(self):
        curses_color = False

        # Start connection to server
        game_client = GameClient('127.0.0.1', 1403)
        game_client.start()
        
        map = 'classic'
        players = [{
                "id": 0,
                "name": 'dani',
                "aesthetics": {
                        "char":"x", 
                        "color_tail": {
                                "fg": "green", 
                                "bg": "black"
                            }, 
                        "color_head": {
                                "fg": "green", 
                                "bg": "green"
                            }
                    }
            }]
        computers = []
        flush_input = 0
        refresh_rate = 0.3

        # TODO: Resolve after doing the room thing
        players[0]['id'] = game_client.player_id

        # Start the game
        game_state, colors = game_client.start_game(map, players, computers, flush_input, refresh_rate)

        if game_state == GameState.STARTED:
            curses.cbreak()
            # Create a new pad to display the game
            game_curses_pad = curses.newpad(125, 125)

            if curses.has_colors():
                curses.start_color()
                curses_color = True

                # Initialize all colors
                for color in colors:
                    curses.init_pair(color.get("number"), utils.parseColor(color.get("fg")), utils.parseColor(color.get("bg")))

            # Start input thread
            input_thread = InputThread(game_client, game_curses_pad)
            input_thread.start()
            
        while game_state == GameState.STARTED:
            drawn_map, game_state, winner = game_client.query_game()

            game_curses_pad.clear()
            drawField(game_curses_pad, drawn_map, curses_color)

            # Update screen size
            scr_height, scr_width = self.screen.getmaxyx()

            # Try to draw the pad
            try:
                game_curses_pad.refresh(0,0 , 0,0 , scr_height-1,scr_width-1)
            except Exception:
                curses.nocbreak()
                curses.endwin()
                print(str(scr_height) + ", " + str(scr_width))
                sys.exit(1)

            time.sleep(0.03)

        self.screen.clear()
        self.screen.addstr("\n\nGame ended!\n")

        if winner:
            self.screen.addstr(winner + " WON!!!!")

        self.screen.refresh()

        game_client.kill.set()
        input_thread.kill.set()

        time.sleep(2)

if __name__ == "__main__":
    curses.wrapper(MyApp)
