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
parser.add_argument("-c", "--curses-refresh", type=float, default=0.07, help="Maximum refresh rate for curses")

args = parser.parse_args()

host = args.host
port = args.port

def drawField(stdscr, drawn_map, curses_color):
    for x in range(len(drawn_map)):
        for y in range(len(drawn_map[x])):
            if curses_color:
                stdscr.addstr(text2art(drawn_map[x][y][0], font='cjk'), curses.color_pair(drawn_map[x][y][1]))
            else:
                stdscr.addstr(text2art(drawn_map[x][y][0], font='cjk'))
        stdscr.addstr('\n')

def displayScore(stdscr, score):
    stdscr.addstr("\nScore:\n")
    for line in score:
        name = line.get("name")
        score = line.get("score")
        
        stdscr.addstr(">> " + name + ':\t' + str(score))
        stdscr.addstr('\n')

def displayError(stdscr, error):
    stdscr.clear()
    stdscr.addstr("\nERROR:\n\t" + error)
    stdscr.refresh()

    time.sleep(3)


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
            for y_banner, line in enumerate(banner.splitlines(), int(y/2 - 3 - len(banner.splitlines()))):
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
        main_menu = tui.Menu(main_menu_items, int(y/2.2), int(x/2.2), self.screen)
        main_menu.items[-1] = ("exit", "exit")
        main_menu.display()

    def display_rooms_menu(self):
        self.screen.clear()

        rooms_submenu_items = [("(option) create room", self.create_room), ("(option) refresh", self.refresh_rooms_menu)]

        try:
            rooms = self.exec_try_n_times(self.game_client.query_rooms, 3)
        except RuntimeError:
            return

        for room in rooms:
            room_name = "(" + str(room.get("player_count")) + "/2) " + room.get("name")
            def room_join():
                self.join_room(room.get("id"))

            rooms_submenu_items.append((room_name, room_join))            

        y, x = self.screen.getmaxyx()
        self.rooms_player_count = tui.PanelList(int(y/2.2) + 2, int(x/2.2) + 10, [str(r.get("player_count")) for r in rooms], self.screen)
        self.rooms_player_count.display()

        self.rooms_submenu = tui.Menu(rooms_submenu_items, int(y/2.2), int(x/2.2), self.screen)
        self.rooms_submenu.display()

        self.rooms_player_count.hide()

    def refresh_rooms_menu(self):
        self.screen.clear()

        rooms_submenu_items = [("(option) create room", self.create_room), ("(option) refresh", self.refresh_rooms_menu)]

        try:
            rooms = self.exec_try_n_times(self.game_client.query_rooms, 3)
        except RuntimeError:
            return

        for room in rooms:
            room_name = "(" + str(room.get("player_count")) + "/2) " + room.get("name")
            def room_join():
                self.join_room(room.get("id"))

            rooms_submenu_items.append((room_name, room_join))        

        self.rooms_submenu.set_items(rooms_submenu_items)
    
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

            y, x = self.screen.getmaxyx()

            if self.game_client.is_host_in_room(room_data):
                room_option = tui.OptionsBox(int(y * 4/5), int(x/3), self.screen, "", ["start", "delete"], False)
                
            else:
                room_option = tui.OptionsBox(int(y * 4/5), int(x/3), self.screen, "", [], False)

            room_option.items[-1] = "back"
            
            # This is a way so that the client can constantly query for more room information
            # ~~~FUcc the blocking getch()


            while True:
                # Initialize/Update display if we have any changes in data
                if not last_room_data == room_data:
                    player_names = [r.get("name") for r in room_data.get("players")]

                    items = ["PLAYER LIST", "======================", " "]
                    items.extend(player_names)
                    player_list = tui.PanelList(int(y/4), int(x/3), items, self.screen)
                    player_list.set_window_size(20, 40)
                    player_list.display()

                    items = ["OPTIONS", "======================", " "]
                    items.append("STATUS: " + int_to_string(room_data.get("game_state")))
                    items.append("MAP: " + room_data.get("map"))
                    items.append("FLUSH?: " + str(room_data.get("flush_input")))
                    items.append("REFRESH: " + str(room_data.get("refresh_rate")))
                    items.append("HOST: " + room_data.get("host_name"))
                    items.append("PLAYERS: " + str(room_data.get("player_count")))
                    options_list = tui.PanelList(int(y/4), int(x/2), items, self.screen)
                    options_list.set_window_size(20, 30)
                    options_list.display()

                    last_room_data = room_data

                # Display options menu in async mode (it doesn't block)
                chs = room_option.display_async()

                if chs == 'start':
                    try:
                        self.exec_try_n_times(lambda: self.game_client.start_game(room_data.get("id")), 3)
                    except RuntimeError:
                        chs = 'back'
                elif chs == 'delete': 
                    try:
                        deleted_successfully = self.exec_try_n_times(self.game_client.delete_room, 3)
                    except RuntimeError:
                        return
                    finally:
                        if not deleted_successfully:
                            displayError(self.screen, "The room was not deleted successfully!")

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

    def create_room(self):
        name, map, f_input, refresh_rate = self.display_create_room_dialog()

        
        exec_create = lambda:   self.game_client.create_room(name, map, [], f_input, refresh_rate)
    
        try:
            room_id = self.exec_try_n_times(exec_create, 3)
        except RuntimeError:
            return

        self.refresh_rooms_menu()
        self.join_room(room_id)

    def display_create_room_dialog(self):
        self.screen.clear()
        y, x = self.screen.getmaxyx()

        name_dialog = tui.InputBox(int(y/2)-3, int(x/2)-10, self.screen, "Name for room:")
        name_dialog.set_window_size(7, 20)
        name = name_dialog.display()

        chosen_map = None
        f_input = False
        refresh_rate = 0.5

        map_submenu = tui.OptionsBox(int(y/2.2), int(x/2.2), self.screen, "Choose map:", ['classic', 'duel', 'survival'])
        chosen_map = map_submenu.display()
        if chosen_map == 'abort':
            return
        
        finput_option = tui.OptionsBox(int(y/2.2), int(x/3.2), self.screen, "Flush input?", ['yes', 'no'], vertical=False)
        f_input = finput_option.display()
        if f_input == 'abort':
            return
        elif f_input == 'yes':
            f_input = True
        else:
            f_input = False

        refresh_rate_input = tui.InputBox(int(y/2.2), int(x/2.2), self.screen, "Refresh rate:")
        refresh_rate_input.set_window_size(7, 20)
        refresh_rate = float(refresh_rate_input.display())

        return name, chosen_map, f_input, refresh_rate

    def display_settings_menu(self):
        self.screen.clear()

        settings_submenu_items = [("change naem", self.change_name), ("change aEStHethiCs", self.change_appearence)]         

        y, x = self.screen.getmaxyx()

        self.settings_submenu = tui.Menu(settings_submenu_items, int(y/2.2), int(x/2.2), self.screen)
        self.settings_submenu.display()

    # Make permanent
    def change_name(self):
        self.screen.clear()

        y, x = self.screen.getmaxyx()
        name_input = tui.InputBox(int(y/2.2), int(x/2.2), self.screen, prompt="New name:")
        name_input.set_window_size(7, 20)
        self.game_client.settings['name'] = str(name_input.display())

        self.game_client.store_settings()

    def change_appearence(self):
        self.screen.clear()
        
        y, x = self.screen.getmaxyx()
        character_input = tui.InputBox(int(y/2 - 4), int(x/2 - 30), self.screen, prompt="Character: (some characters may not work, for example g)")
        character_input.set_window_size(7, 60)
        self.game_client.settings['aesthetics']['char'] = str(character_input.display())

        color_options = tui.OptionsBox(int(y/2.2), int(x/3), self.screen, "Color TAIL - FOREGROUND: ", ["black", "white", "red", "blue", "green", "magenta", "cyan", "yellow"])
        tail_fg = color_options.display()

        color_options.prompt = "Color TAIL - BACKGROUND:"
        tail_bg = color_options.display()

        color_options.prompt = "Color HEAD - FOREGROUND:"
        head_fg = color_options.display()

        color_options.prompt = "Color HEAD - BACKGROUND:"
        head_bg = color_options.display()

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
        curses_refresh = max(0.07, args.curses_refresh)

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

                game_curses_pad.clear()
                drawField(game_curses_pad, drawn_map, curses_color)
                displayScore(game_curses_pad, score_data)

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
