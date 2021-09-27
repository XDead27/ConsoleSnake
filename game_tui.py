import curses, time, sys
import Resources.utils as utils
import Resources.tui as tui
from game_client import GameClient, InputThread
from game import GameState, int_to_string
from art import text2art
import argparse as ap

host = '127.0.0.1'
port = 1403

# Parse flags and arguments
parser = ap.ArgumentParser(description='Snek gaem with frends :>')
parser.add_argument("-p", "--port", type=int, default=1403, help="Port to connect to")
parser.add_argument("-b", "--host", default="127.0.0.1", help="Host ip address to connect to")
parser.add_argument("-c", "--curses-refresh", type=float, default=0.01, help="Maximum refresh rate for curses")

args = parser.parse_args()

host = args.host
port = args.port

# Function that compares both fields and returns an array of 
# positions for the differences and their new values
def compareFields(init_field, post_field):
    if init_field == None:
        init_field = [[[0, 0] for j in range(len(post_field))] for i in range(len(post_field))]

    if (len(init_field) != len(post_field)) or (len(init_field[0]) != len(post_field[0])):
        raise RuntimeError("Comparing fields of different size!")

    diff_fields = []
    for x in range(len(init_field)):
        # weird_spaces_counter = 0
        for y in range(len(init_field[x])):
            if not init_field[x][y] == post_field[x][y]:
                diff_fields.append([x, 2 * y, post_field[x][y][0], post_field[x][y][1]]) 
            # if post_field[x][y][0] == "  ":
                # weird_spaces_counter += 1

    return diff_fields

def drawField(stdscr, init_map, post_map, curses_color):
    diff_fields = compareFields(init_map, post_map)
    for difference in diff_fields:
        y = difference[0]
        x = difference[1]
        c = difference[2]
        color = difference[3]
        
        if curses_color:
            stdscr.addstr(y, x, text2art(c, font='cjk'), curses.color_pair(color))
        else:
            stdscr.addstr(y, x, text2art(c, font='cjk'))

def displayScore(stdscr, score, start_position=20):
    stdscr.addstr(start_position, 1, "Score:\n\n")
    for line in score:
        name = line.get("name")
        score = line.get("score")
        
        stdscr.addstr(" >> " + name + ':\t' + str(score))
        stdscr.addstr('\n')

def displayError(stdscr, error):
    stdscr.clear()
    stdscr.addstr("\nERROR:\n\t")
    for line in error.splitlines():
        stdscr.addstr(line + "\n\t")
    stdscr.refresh()

    time.sleep(3)

    stdscr.clear()
    stdscr.refresh()


class ConsoleSnakeApp(object):
    def __init__(self, stdscreen):
        self.screen = stdscreen
        self.error_counter = 0

        # Start connection to server
        self.game_client = GameClient(host, port)
        self.game_client.start()

        self.display_start_menu()

        self.game_client.kill.set()

    # Wrapper function (?) that executes a function <iters> times
    # If the function returns a value in <error_msg> or raises an exception
    # this function will try to run it a few more times until giving up
    #
    # Probably a monstruosity 
    def exec_try_n_times(self, handle, iters):
        while self.error_counter < iters:
            try:
                data, error_msg = handle()

                if not error_msg:
                    self.error_counter = 0
                    return data
                self.error_counter += 1
            except Exception as e:
                self.error_counter += 1
                if self.error_counter == iters:
                    error_msg = repr(e)  
                continue

        self.error_counter = 0
        displayError(self.screen, error_msg)

        raise RuntimeError("Could not run function!")

    def display_start_menu(self):
        curses.curs_set(0)

        y, x = self.screen.getmaxyx()

        # for the aesthetic
        banner = text2art("snek", font="impossible")

        # find the size of the banner
        for line in banner.splitlines():
            max_len = 0
            if len(line) > max_len:
                max_len = len(line)

        try:
            for y_banner, line in enumerate(banner.splitlines(), int(y/2 + 2 - len(banner.splitlines()))):
                self.screen.addstr(y_banner, int(x/2 - max_len/2), line)
        except Exception:
            # if we cannot draw the banner, do not draw it :)
            pass

        self.screen.refresh()

        # TODO: maybe make this an options box
        main_menu_items = [
            ("play", self.display_rooms_menu),
            ("settings", self.display_settings_menu),
        ]
        main_menu = tui.Menu(main_menu_items, int(2*y/3), int(x/2), self.screen, size_y=5, size_x=14, border=(0, 0, " ", " ", 0, 0, 0, 0))
        main_menu.items[-1] = ("exit", "exit")
        main_menu.display()

    def display_rooms_menu(self):
        self.screen.clear()

        rooms_submenu_items = [("(option) create room", self.create_room), ("(option) refresh", self.refresh_rooms_menu)]

        try:
            rooms = self.exec_try_n_times(self.game_client.query_rooms, 3)
        except RuntimeError:
            return

        room_ids = [room.get("id") for room in rooms]

        for room in rooms:
            room_name = "(" + str(room.get("player_count")) + "/2) " + room.get("name")

            # In case you are wondering, here I am doing a very illegal thing and accessing .position from a thing that does
            # not yet exist. Apparently lambda functions do not pair well with variable arguments in a loop :)
            # The -2 is there to take into account the 'create room' and 'refresh' entries
            rooms_submenu_items.append((room_name, lambda: self.join_room(room_ids[self.rooms_submenu.position - 2])))

        y, x = self.screen.getmaxyx()
        self.rooms_submenu = tui.Menu(rooms_submenu_items, int(y/2), int(x/2), self.screen, \
                                      size_y=len(rooms_submenu_items) + 3, size_x=30, \
                                      border=(0, 0, " ", " ", 0, 0, 0, 0))
        self.rooms_submenu.display()


    def refresh_rooms_menu(self):
        self.screen.clear()

        rooms_submenu_items = [("(option) create room", self.create_room), ("(option) refresh", self.refresh_rooms_menu)]

        try:
            rooms = self.exec_try_n_times(self.game_client.query_rooms, 3)
        except RuntimeError:
            return

        room_ids = [room.get("id") for room in rooms]

        for room in rooms:
            room_name = "(" + str(room.get("player_count")) + "/2) " + room.get("name")

            # In case you are wondering, here I am doing a very illegal thing and accessing .position from a thing that does
            # not yet exist. Apparently lambda functions do not pair well with variable arguments in a loop :)
            # The -2 is there to take into account the 'create room' and 'refresh' entries
            rooms_submenu_items.append((room_name, lambda: self.join_room(room_ids[self.rooms_submenu.position - 2])))       

        self.rooms_submenu.set_items(rooms_submenu_items)
        # y, x = self.screen.getmaxyx()
        self.rooms_submenu.set_window_size(len(rooms_submenu_items) + 2, 30)
    
    def join_room(self, room_id):
        try:
            room_data = self.exec_try_n_times(lambda: self.game_client.join_room(room_id), 3)
        except RuntimeError:
            return

        self.display_room(room_data)

        self.screen.clear()
        self.screen.refresh()

    def display_room(self, room_data):
        self.screen.clear()
        
        while True:
            last_room_data = None
            ask_refresh = False

            y, x = self.screen.getmaxyx()

            try:
                if self.game_client.is_host_in_room(room_data):
                    max_x = self.screen.getmaxyx()[1]
                    room_option = tui.OptionsBox(int(y * 4/5), int(x/2), self.screen, "", ["start", "configure", "delete"], False, size_y=6, size_x=min(68, max_x))
                else:
                    room_option = tui.OptionsBox(int(y * 4/5), int(x/2), self.screen, "", [], False, size_y=6, size_x=8)
            except Exception as e:
                displayError(self.screen, repr(e))
                return
                
            
            room_option.items[-1] = "back"
            
            # This is a way so that the client can constantly query for more room information
            # ~~~FUcc the blocking getch()


            while True:
                # Initialize/Update display if we have any changes in data
                if (not last_room_data == room_data) or ask_refresh:
                    player_names = [r.get("name") for r in room_data.get("players")]

                    items = ["PLAYER LIST", "======================", " "]
                    items.extend(player_names)

                    items2 = ["OPTIONS", "======================", " "]
                    items2.append("STATUS: " + int_to_string(room_data.get("game_state")))
                    items2.append("MAP: " + room_data.get("map"))
                    items2.append("HOST: " + room_data.get("host_name"))
                    items2.append("PLAYERS: " + str(room_data.get("player_count")))
                    items2.append("-")
                    items2.extend([option.upper().replace("_", " ") + ": " + str(room_data.get("options").get(option)) for option in room_data.get("options")])

                    size_y = max(len(player_names), len(items))
                    player_list = tui.PanelList(int(y/2), int(x/2) - 15, items, self.screen, size_y + 10, size_x=30, border=(" ", ".", 0, 0,0,0,0,0))
                    player_list.display()
                    options_list = tui.PanelList(int(y/2), int(x/2) + 15, items2, self.screen, size_y + 10, size_x=30, border=(" ", 0," "," ", " ", 0, " ", 0))
                    options_list.display()

                    last_room_data = room_data
                    ask_refresh = False

                # Display options menu in async mode (it doesn't block)
                chs = room_option.display_async()[0]

                if chs == 'start':
                    try:
                        self.exec_try_n_times(lambda: self.game_client.start_game(room_data.get("id")), 3)
                    except RuntimeError:
                        chs = 'back'
                elif chs == 'configure':
                    self.display_configuration_menu(room_data.get("options"))
                    ask_refresh = True
                elif chs == 'delete': 
                    try:
                        deleted_successfully = self.exec_try_n_times(self.game_client.delete_room, 3)
                    except RuntimeError:
                        return
                    finally:
                        if not deleted_successfully:
                            displayError(self.screen, "The room was not deleted successfully!")

                        self.refresh_rooms_menu()
                        player_list.hide() 
                        return
                elif chs == 'back':
                    try:
                        self.exec_try_n_times(self.game_client.leave_room, 10)
                    except RuntimeError:
                        return
                    
                    player_list.hide() 
                    return
                
                # Check if something changed
                try:
                    room_data = self.exec_try_n_times(self.game_client.check_room_updates, 3)
                except RuntimeError:
                    try:
                        self.exec_try_n_times(self.game_client.leave_room, 10)
                    except RuntimeError:
                        return
                    
                    player_list.hide() 
                    print(room_data)
                    time.sleep(2)
                    return


                # If game started, start game
                if room_data.get("game_state") == 1:
                    self.play_game(room_data.get("id"))
                    player_list.hide() 
                    break

                time.sleep(max(0.1, args.curses_refresh))

            player_list.hide() 
        return

    def display_configuration_menu(self, room_options):
        self.screen.clear()

        while True:
            y, x = self.screen.getmaxyx()

            configuration_items = [option for option in room_options]
            configuration_values = [str(room_options.get(option)) for option in room_options]
            config_values = tui.PanelList(int(y/2), int(x/2) + 10, configuration_values, self.screen, len(configuration_values) + 4, size_x=10)
            config_values.display()

            set_option = tui.OptionsBox(int(y/2)-2, int(x/2) - 5, self.screen, "", configuration_items, vertical=True, size_y=len(configuration_items) + 6, size_x=15)
            set_option.items[-1] = "done"
            chs = set_option.display()

            if chs[0] == "done":
                break

            new_value = self.display_set_option_dialog(chs[0])

            room_options[chs[0]] = new_value

        try:
            self.exec_try_n_times(lambda: self.game_client.set_room_options(room_options), 3)
        except RuntimeError:
            self.screen.clear()
            return

        self.screen.clear()

    def display_set_option_dialog(self, option_to_set):
        y, x = self.screen.getmaxyx()

        option_dialog = tui.InputBox(int(y/2), int(x/2), self.screen, "New value:", size_y=7, size_x=20)
        option_dialog.window.clear()
        value = option_dialog.display()

        option_dialog.hide()

        return value

    def create_room(self):
        try:
            name, map, f_input, refresh_rate = self.display_create_room_dialog()
            room_id = self.exec_try_n_times(lambda: self.game_client.create_room(name, map, [], f_input, refresh_rate), 3)
        except Exception:
            return

        self.refresh_rooms_menu()
        self.join_room(room_id)

    def display_create_room_dialog(self):
        self.screen.clear()
        y, x = self.screen.getmaxyx()

        name_dialog = tui.InputBox(int(y/2), int(x/2), self.screen, "Name for room:", size_y=7, size_x=20)
        name = name_dialog.display()

        chosen_map = None
        f_input = False
        refresh_rate = 0.5

        map_submenu = tui.OptionsBox(int(y/2), int(x/2), self.screen, "Choose map:", ['classic', 'duel', 'survival'], size_y=9, size_x=15)
        chosen_map = map_submenu.display()[0]
        if chosen_map == 'abort':
            return

        f_input = True

        refresh_rate_input = tui.InputBox(int(y/2), int(x/2), self.screen, "Refresh rate:", size_y=7, size_x=20)
        refresh_rate = float(refresh_rate_input.display())

        return name, chosen_map, f_input, refresh_rate

    def display_settings_menu(self):
        self.screen.clear()

        settings_submenu_items = [("change naem", self.change_name), ("change aEStHethiCs", self.change_appearence)]         

        y, x = self.screen.getmaxyx()

        self.settings_submenu = tui.Menu(settings_submenu_items, int(y/2), int(x/2), self.screen, size_y=4, size_x=25)
        self.settings_submenu.display()

    # Make permanent
    def change_name(self):
        self.screen.clear()

        y, x = self.screen.getmaxyx()
        name_input = tui.InputBox(int(y/2), int(x/2), self.screen, prompt="New name:", size_y=7, size_x=20)
        self.game_client.settings['name'] = str(name_input.display())

        self.game_client.store_settings()

    def change_appearence(self):
        self.screen.clear()
        
        y, x = self.screen.getmaxyx()
        character_input = tui.InputBox(int(y/2), int(x/2), self.screen, prompt="Character: (some characters may not work, for example g)", size_y=7, size_x=60)
        self.game_client.settings['aesthetics']['char'] = str(character_input.display())

        color_options = tui.OptionsBox(int(y/2), int(x/2), self.screen, \
                                        "Color TAIL - FOREGROUND: ", ["black", "white", "red", "blue", "green", "magenta", "cyan", "yellow"], \
                                        size_y=20, size_x=25)
        tail_fg = color_options.display()[0]

        color_options.prompt = "Color TAIL - BACKGROUND:"
        tail_bg = color_options.display()[0]

        color_options.prompt = "Color HEAD - FOREGROUND:"
        head_fg = color_options.display()[0]

        color_options.prompt = "Color HEAD - BACKGROUND:"
        head_bg = color_options.display()[0]

        self.game_client.settings['aesthetics']['color_tail'] = {
                "fg": tail_fg,
                "bg": tail_bg
            }

        self.game_client.settings['aesthetics']['color_head'] = {
                "fg": head_fg,
                "bg": head_bg
            }

        self.game_client.store_settings()

    def play_game(self, room_id):
        self.screen.clear()
        
        curses_color = False

        # Start the game
        try:
            game_state, colors = self.exec_try_n_times(lambda: self.game_client.get_game_vars(room_id), 3)
        except RuntimeError:
            return
        
        winner = None
        last_drawn_map = None
        curses_refresh = max(0.001, args.curses_refresh)

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
                try:
                    drawn_map, game_state, winner, score_data = self.exec_try_n_times(self.game_client.query_game, 3)
                except RuntimeError:
                    break

                # game_curses_pad.clear()
                drawField(game_curses_pad, last_drawn_map, drawn_map, curses_color)
                displayScore(game_curses_pad, score_data, len(drawn_map) + 5)
                last_drawn_map = drawn_map

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

                time.sleep(curses_refresh)

            self.screen.clear()

            if winner:
                self.screen.addstr("\n\nGame ended!\n")
                self.screen.addstr(winner + " WON!!!!")

                self.screen.refresh()

                time.sleep(2)

            input_thread.kill.set()

            game_curses_pad.clear()
            self.screen.clear()

if __name__ == "__main__":
    curses.wrapper(ConsoleSnakeApp)
