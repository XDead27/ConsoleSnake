#!/usr/bin/env python

import curses, time, sys
import Resources.utils as utils
import Resources.menu as menu
from game_client import GameClient, InputThread
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

class ConsoleSnakeApp(object):
    def __init__(self, stdscreen):
        self.screen = stdscreen


        # Start connection to server
        self.game_client = GameClient('127.0.0.1', 1403)
        self.game_client.start()

        self.display_start_menu()

        self.game_client.kill.set()

    def display_start_menu(self):
        curses.curs_set(0)

        y, x = self.screen.getmaxyx()

        main_menu_items = [
            ("play", self.display_rooms_menu),
            ("settings", curses.flash),
        ]
        main_menu = menu.Menu(main_menu_items, int(y/2.2), int(x/2.2), self.screen)
        main_menu.display()

    def display_rooms_menu(self):
        rooms_submenu_items = [("create room", self.create_room), ("refresh", self.refresh_rooms_menu)]

        rooms = self.game_client.query_rooms()

        for room in rooms:
            room_name = room.get("name")
            def room_join():
                self.join_room(room.get("id"))

            rooms_submenu_items.append((room_name, room_join))            

        y, x = self.screen.getmaxyx()
        self.rooms_player_count = menu.PanelList(int(y/2.2) + 2, int(x/2.2) + 10, [str(r.get("player_count")) for r in rooms], self.screen)
        self.rooms_player_count.display()

        self.rooms_submenu = menu.Menu(rooms_submenu_items, int(y/2.2), int(x/2.2), self.screen)
        self.rooms_submenu.display()

        self.rooms_player_count.hide()

    def refresh_rooms_menu(self):
        rooms_submenu_items = [("create room", self.create_room), ("refresh", self.refresh_rooms_menu)]

        rooms = self.game_client.query_rooms()

        for room in rooms:
            room_name = room.get("name")
            def room_join():
                self.join_room(room.get("id"))

            rooms_submenu_items.append((room_name, room_join))            

        self.rooms_submenu.set_items(rooms_submenu_items)
    
    def join_room(self, room_id):
        room_data = self.game_client.join_room(room_id)

        self.display_room(room_data)

    def display_room(self, room_data):
        player_names = [r.get("name") for r in room_data.get("players")]

        y, x = self.screen.getmaxyx()
        items = ["PLAYER LIST", "======================", " "]
        items.extend(player_names)
        player_list = menu.PanelList(int(y/4), int(x/3), items, self.screen)
        player_list.display()

        def play_game():
            self.play_game(room_data.get("id"))

        room_menu = menu.Menu([("start", play_game)], int(y * 4/5), int(x/3), self.screen, False)
        room_menu.items[-1] = ("back", "exit")
        room_menu.display()   

        player_list.hide()  

    def create_room(self):
        name, map, f_input, refresh_rate = self.display_create_room_dialog()

        self.game_client.create_room(name, map, [], f_input, refresh_rate)

        self.refresh_rooms_menu()

    def display_create_room_dialog(self):
        y, x = self.screen.getmaxyx()

        name_dialog = menu.InputBox(int(y/2)-3, int(x/2)-10, self.screen, "Name for room:")
        name_dialog.set_window_size(7, 20)
        name = name_dialog.display()

        chosen_map = None
        f_input = False
        refresh_rate = 0.5

        map_submenu = menu.OptionsBox(int(y/2.2), int(x/2.2), self.screen, "Choose map:", ['classic', 'duel', 'survival'])
        chosen_map = map_submenu.display()
        if chosen_map == 'abort':
            return
        
        finput_option = menu.OptionsBox(int(y/2.2), int(x/2.2), self.screen, "Flush input?", ['yes', 'no'], vertical=False)
        f_input = finput_option.display()
        if chosen_map == 'abort':
            return
        elif chosen_map == 'yes':
            f_input = True
        elif chosen_map == 'no':
            f_input = False

        refresh_rate_input = menu.InputBox(int(y/2.2), int(x/2.2), self.screen, "Refresh rate:")
        refresh_rate_input.set_window_size(7, 20)
        refresh_rate = float(refresh_rate_input.display())

        return name, chosen_map, f_input, refresh_rate

    def play_game(self, room_id):
        curses_color = False

        # Start the game
        game_state, colors = self.game_client.start_game(room_id)

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
            input_thread = InputThread(self.game_client, game_curses_pad)
            input_thread.start()
            
        while game_state == GameState.STARTED:
            drawn_map, game_state, winner = self.game_client.query_game()

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

        self.game_client.kill.set()
        input_thread.kill.set()

        time.sleep(2)

        game_curses_pad.clear()

if __name__ == "__main__":
    curses.wrapper(ConsoleSnakeApp)
