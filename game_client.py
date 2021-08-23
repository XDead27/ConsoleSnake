#!/usr/bin/env python3

import sys
import socket
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
logfile = 'Logs/client.log'
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

my_handler = RotatingFileHandler(logfile, mode='a', maxBytes=5*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)

client_log = logging.getLogger('root')
client_log.setLevel(logging.DEBUG)

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

        # TODO
        self.settings = {
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
            }

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
        client_log.info("Waiting for response with ack {" + str(wanted_ack) + "} ...")
        while not wanted_ack in self.responses.keys():
            # Do not waste cpu cycles
            time.sleep(0.01)

        client_log.info("Got response with ack {" + str(wanted_ack) + "}. Stopped waiting!")

        wanted_response = self.responses[wanted_ack]
        self.responses.pop(wanted_ack)
        return wanted_response

    def create_room(self, name, map, computers, f_input, refresh_rate):
        action = "create_room"
        value = {
                "name": name,
                "map": map,
                "computers": [],
                "f_input": f_input,
                "refresh": refresh_rate
            }

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        if response_action == "notice":
            client_log.info(response_value.get("message"))
            if response_value.get("room_id"):
                self.current_game_id = response_value.get("room_id")
                client_log.info("Game ID: " + str(self.current_game_id))
                return self.current_game_id
            else:
                client_log.error("Room did not create successfully!")
                return None

        
    def join_room(self, room_id):
        action = "join_room"
        value = {
                "room_id": room_id,
                "settings": self.settings
            }

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        if response_action == "notice":
            client_log.info(response_value.get("message"))
            if response_value.get("player_id"):
                self.player_id = response_value.get("player_id")
                client_log.info("Player ID: " + str(self.player_id))
                client_log.debug("Other players in room: " + str(response_value.get("room_data").get("players")))
                self.current_game_id = room_id
                return response_value.get("room_data")
            else:
                client_log.error("Did not join successfully!")
                return None

    def leave_room(self):
        action = "leave_room"
        value = {
                "room_id": self.current_game_id,
                "player_id": self.player_id
            }
        
        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        if response_action == "notice":
            client_log.info(response_value.get("message"))

    def delete_room(self):
        action = "delete_room"
        value = {
                "room_id": self.current_game_id,
                "player_id": self.player_id
            }

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        if response_action == "notice":
            client_log.info(response_value.get("message"))

    def start_game(self, room_id):
        action = "start_game"
        value = {
                "room_id": room_id
            }

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        game_state = GameState.NOT_STARTED
        colors = []

        if response_action == "notice":
            client_log.info(response_value.get("message"))
            if response_value.get("game_id"):
                self.current_game_id = response_value.get("game_id")
                client_log.info("Game ID: " + str(self.current_game_id))
                game_state = GameState.STARTED
            
            if response_value.get("colors"):
                colors = response_value.get("colors")

        return game_state, colors

    def query_game(self):
        action = "query"
        value = {"game_id": self.current_game_id}

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        drawn_map = []
        winner = ''
        if response_action == "notice":
            client_log.error(response_value.get("message"))
            game_state = GameState.ERROR
        elif response_action == "update":
            drawn_map = response_value.get("drawn_map")
            game_state = response_value.get("game_state")
            winner = response_value.get("winner")

        return drawn_map, game_state, winner

    def send_input(self, input):
        action = "input"
        value = {
                "game_id": self.current_game_id,
                "player_id": self.player_id,
                "input": input
            }

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        # if response_action == "notice":
        #     client_log.info(response_value.get("message"))

        # return self.query_game()

    def query_rooms(self):
        action = "query_rooms"
        value = {}

        # Send a new request
        request = libclient.create_request(action, value)
        seq = self.place_request(request)

        response = self.wait_for_response(seq)

        response_action = response.get("action")
        response_value = response.get("value")

        room_data = []
        if response_action == "notice":
            client_log.error(response_value.get("message"))
            return None
        elif response_action == "room_list":
            room_data = response_value.get("room_data")

        return room_data

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
                input_raw = self.stdscr.getch()
            except Exception:
                break
            filtered_input = self.filterInput(input_raw)

            if not filtered_input == None:
                self.game_client.send_input(filtered_input)


def get_user_request():
    map = input("Map (classic, duel, survival): ")
    n_players = int(input("Number of players: "))
    players = []
    computers = []
    for x in range(n_players):
        name = input("Player " + str(x) + " name: ")
        # TODO: With aesthetics
        player_info = {
                "id": x,
                "name": name,
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
        
        players.append(player_info)
    flush_input = bool(input("Flush input?: "))
    refresh = float(input("Refresh rate: "))
    
    return map, players, computers, flush_input, refresh
