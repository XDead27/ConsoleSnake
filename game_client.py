import sys, os
import socket, json
import selectors
import traceback
import threading, time, curses, random, logging
from logging.handlers import RotatingFileHandler
from art import text2art
import Resources.utils as utils

import Networking.libclient as libclient
from game import GameState
from Resources.snek import Direction

# TODO: maybe extirpate this
logfolder = os.environ['HOME'] + '/.local/share/consolesnake/Logs'
logfile = logfolder + '/client.log'

if not os.path.exists(logfile):
    os.makedirs(logfolder)

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

my_handler = RotatingFileHandler(logfile, mode='a', maxBytes=5*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

client_log = logging.getLogger('root')
client_log.setLevel(logging.INFO)

client_log.addHandler(my_handler)

class GameClient(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.kill = threading.Event()

        self.sel = selectors.DefaultSelector()
        self.current_game_id = None
        self.player_id = None

        self.host = host
        self.port = port
        self.response_handler = self.process_response

        self.prot_conn = None
        self.responses = {}
        self.last_response = None

        self.settings = {
                "name": 'wanderer',
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
            }

        self.restore_settings()

    def start_connection(self):
        addr = (self.host, self.port)
        client_log.info("starting connection to " + str(addr))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(True)
        sock.connect_ex(addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        prot_conn = libclient.Connection(self.sel, sock, addr, response_handler=self.response_handler, logger=client_log)
        self.sel.register(sock, events, data=prot_conn)

        client_log.debug("Protocol connection: " + repr(prot_conn))

        return prot_conn

    def place_request(self, request):
        init_time = time.time()
        timeout_time = 5
        while not self.prot_conn and time.time() - init_time < timeout_time:
            client_log.debug("No connection established... Retrying in 0.5s!")
            time.sleep(0.5)

        if not self.prot_conn:
            client_log.error("No connection established!")
            return None

        client_log.info("Placing request: " + repr(request))
        return self.prot_conn.place_request(request)

    def process_response(self, content, ack):
        self.responses[ack] = content

        client_log.info("Processed response(ack, action): " + str(ack) + ", " + repr(content.get("action")))

    def wait_for_response(self, wanted_ack):
        client_log.debug("Waiting for response with ack {" + str(wanted_ack) + "} ...")
        start_time = time.time()
        while (not wanted_ack in self.responses.keys()) and time.time() - start_time < 1.0:
            # Do not waste cpu cycles
            time.sleep(0.01)

        if time.time() - start_time > 1.0:
            wanted_response = None
        else:
            client_log.debug("Got response with ack {" + str(wanted_ack) + "}. Stopped waiting!")

            wanted_response = self.responses[wanted_ack]
            self.responses.pop(wanted_ack)

        return wanted_response

    def send_message(self, action, value):
        response_action = None
        response_value = None
        error_msg = None
        
        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        if response:
            response_action = response.get("action")
            response_value = response.get("value")
        else:
            error_msg = "Request timed out or connection was severed!"

        return response_action, response_value, error_msg

    def create_room(self, name, map, computers, f_input, refresh_rate):
        action = "create_room"
        value = {
                "name": name,
                "map": map,
                "computers": [],
                "f_input": f_input,
                "refresh": refresh_rate
            }

        response_action, response_value, error_msg = self.send_message(action, value)

        if response_action == "notice":
            client_log.info(response_value.get("message"))
            self.current_game_id = response_value.get("room_id")
            client_log.info("Game ID: " + str(self.current_game_id))
        elif not error_msg:
            error_msg = "Room did not create successfully!"
            client_log.error(error_msg)

        return self.current_game_id, error_msg

        
    def join_room(self, room_id):
        action = "join_room"
        value = {
                "room_id": room_id,
                "settings": self.settings
            }

        response_action, response_value, error_msg = self.send_message(action, value)
        data = None

        if response_action == "room_update":
            client_log.debug(response_value.get("message"))
            self.player_id = response_value.get("player_id")
            client_log.info("Player ID: " + str(self.player_id))
            client_log.debug("Other players in room: " + str(response_value.get("room_data").get("players")))
            self.current_game_id = room_id
            data = response_value.get("room_data")
        elif not error_msg:
            error_msg = "Did not join successfully!"
            client_log.error(error_msg)

        return data, error_msg

    def check_room_updates(self):
        action = "room_query"
        value = {
                "room_id": self.current_game_id
            }

        response_action, response_value, error_msg = self.send_message(action, value)

        if response_action == "notice":
                client_log.info(response_value.get("message"))
                client_log.error("Room does not exist!")
                error_msg = response_value.get("message")
        elif response_action == "room_update":
                response_value = response_value.get("room_data")


        return response_value, error_msg

    def leave_room(self):
        action = "leave_room"
        value = {
                "room_id": self.current_game_id,
                "player_id": self.player_id
            }
        
        response_action, response_value, error_msg = self.send_message(action, value)
        data = None

        if response_action == "notice":
            data = response_value.get("message")
            client_log.info(data)

        return data, error_msg

    def delete_room(self):
        action = "delete_room"
        value = {
                "room_id": self.current_game_id,
                "player_id": self.player_id
            }

        response_action, response_value, error_msg = self.send_message(action, value)
        data = None

        if response_action == "notice":
            client_log.info(response_value.get("message"))
            # Return true if room was successfully deleted, false otherwise
            if response_value.get("ok"):
                data = True
            else:
                data = False

        return data, error_msg

    def start_game(self, room_id):
        action = "start_game"
        value = {
                "room_id": room_id,
                "player_id": self.player_id
            }

        response_action, response_value, error_msg = self.send_message(action, value)
        data = None

        if response_action == "notice":
            data = response_value.get("message")
            client_log.info(data)

        return data, error_msg

    def get_game_vars(self, game_id):
        action = "get_game_vars"
        value = {
                "game_id": self.current_game_id
            }

        response_action, response_value, error_msg = self.send_message(action, value)
        game_state = GameState.NOT_STARTED
        colors = None

        if response_action == "notice":
            client_log.info(response_value.get("message"))
            client_log.info("Game ID: " + str(self.current_game_id))            
            colors = response_value.get("colors")
            game_state = GameState.STARTED

        return (game_state, colors), error_msg
        
    def query_game(self):
        action = "query"
        value = {"game_id": self.current_game_id}

        response_action, response_value, error_msg = self.send_message(action, value)

        drawn_map = []
        game_state = GameState.ERROR
        winner = ''
        score_data = []

        if response_action == "notice":
            client_log.error(response_value.get("message"))
            error_msg = response_value.get("message")
            game_state = GameState.ERROR
        elif response_action == "update":
            drawn_map = response_value.get("drawn_map")
            game_state = response_value.get("game_state")
            winner = response_value.get("winner")
            score_data = response_value.get("score_data")

        return (drawn_map, game_state, winner, score_data), error_msg

    def send_input(self, input):
        action = "input"
        value = {
                "game_id": self.current_game_id,
                "player_id": self.player_id,
                "input": input
            }
        response_action = None

        try:
            while response_action == None:
                # Send a new request
                request = libclient.create_request(action, value)
                seq = self.place_request(request)

                response = self.wait_for_response(seq)

                response_action = response.get("action")
                response_value = response.get("value")

                if response_action == "notice":
                    client_log.debug("Input registered: (" + str(response_action) + ") " + str(response_value))
        except Exception:
            client_log.error("In GameClient: " + traceback.format_exc())
            pass

    def query_rooms(self):
        action = "query_rooms"
        value = {}
        room_data = []

        response_action, response_value, error_msg = self.send_message(action, value)

        if response_action == "notice":
            error_msg = response_value.get("message")
            client_log.error(error_msg)
        else:
            room_data = response_value.get("room_data")

        return room_data, error_msg

    def is_host_in_room(self, room_data):
        return self.player_id == room_data.get("host").get("id")

    def store_settings(self):
        settings_folder = os.environ['HOME'] + '/.local/share/consolesnake'
        
        settings_path = settings_folder + "/player_settings.json"

        if not os.path.exists(settings_folder):
            os.makedirs(settings_folder)

        with open(settings_path, 'w') as fileHandle:
            json.dump(self.settings, fileHandle)

    def restore_settings(self):
        settings_folder = os.environ['HOME'] + '/.local/share/consolesnake'
        
        settings_path = settings_folder + "/player_settings.json"

        if os.path.exists(settings_path):
            with open(settings_path, 'r') as fileHandle:
                self.settings = json.load(fileHandle)

    def run(self):
        self.prot_conn = self.start_connection()

        while not self.kill.is_set():
            events = self.sel.select(timeout=0.01)
            for key, mask in events:
                prot_conn = key.data
                try:
                    prot_conn.process_events(mask)
                except Exception:
                    client_log.error(
                        "main: error: exception for" + \
                        f"{prot_conn.addr}:\n{traceback.format_exc()}",
                    )
                    prot_conn.close()
            # Check for a socket being monitored to continue.
            if not self.sel.get_map():
                break

        self.sel.close()


class InputThread(threading.Thread):
    def __init__(self, game_client, stdscr):
        threading.Thread.__init__(self)
        self.kill = threading.Event()
        self.game_client = game_client
        self.stdscr = stdscr

    def filterInput(self, raw):
        # TODO: Setup menu for these
        available_inputs = {
                ord('w'): Direction.UP, 
                ord('a'): Direction.LEFT, 
                ord('s'): Direction.DOWN, 
                ord('d'): Direction.RIGHT
            }

        if raw in available_inputs.keys():
            return available_inputs.get(raw)
        else:
            return None

    def run(self):
        self.stdscr.nodelay(False)

        while not self.kill.is_set():
            try:
                client_log.debug("InputThread waiting for input.")
                input_raw = self.stdscr.getch()
                client_log.debug("InputThread got input: " + str(input_raw))
            except Exception:
                client_log.error("In InputThread: " + traceback.format_exc())
                break
            filtered_input = self.filterInput(input_raw)
            client_log.debug("InputThread filtered input: " + repr(filtered_input))

            if filtered_input:
                self.game_client.send_input(filtered_input)
