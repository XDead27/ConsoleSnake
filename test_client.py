#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import threading, time, curses
from art import text2art
import Resources.utils as utils

import Networking.libclient as libclient
from game import GameState

class GameClient(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)

        self.sel = selectors.DefaultSelector()
        self.current_game_id = None

        self.host = host
        self.port = port
        self.response_handler = self.process_response

        self.prot_conn = None
        self.processed_response = False
        self.last_response = None

    def start_connection(self):
        addr = (self.host, self.port)
        print("starting connection to", addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(True)
        sock.connect_ex(addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        prot_conn = libclient.Connection(self.sel, sock, addr, response_handler=self.response_handler)
        self.sel.register(sock, events, data=prot_conn)

        return prot_conn

    def place_request(self, request):
        if(self.prot_conn):
            self.prot_conn.place_request(request)
        else:
            print("No connection established!")

    def process_response(self, content):
        self.processed_response = True
        self.last_response = content

    def wait_for_response(self):
        while not self.processed_response:
            pass

        self.processed_response = False
        return self.last_response

    def start_game(self, map, players, computers, f_input, refresh_rate):
        action = "start_game"
        value = {
                "map": map,
                "players": players,
                "computers": [],
                "f_input": f_input,
                "refresh": refresh_rate
            }

        # Send a new request
        request = libclient.create_request(action, value)
        self.place_request(request)

        response = self.wait_for_response()

        response_action = response.get("action")
        response_value = response.get("value")

        game_state = GameState.NOT_STARTED
        colors = []

        if response_action == "notice":
            print(response_value.get("message"))
            if response_value.get("game_id"):
                self.current_game_id = response_value.get("game_id")
                print("Game ID: " + str(self.current_game_id))
                game_state = GameState.STARTED
            
            if response_value.get("colors"):
                colors = response_value.get("colors")

        return game_state, colors

    def query_game(self):
        action = "query"
        value = {"game_id": self.current_game_id}

        # Send a new request
        request = libclient.create_request(action, value)
        self.place_request(request)

        response = self.wait_for_response()

        response_action = response.get("action")
        response_value = response.get("value")

        drawn_map = []
        if response_action == "notice":
            print(response_value.get("message"))
        elif response_action == "update":
            drawn_map = response_value.get("drawn_map")
            game_state = response_value.get("game_state")
            winner = response_value.get("winner")

        return drawn_map, game_state, winner

    def run(self):
        self.prot_conn = self.start_connection()

        try:
            while True:
                events = self.sel.select(timeout=0.3)
                for key, mask in events:
                    prot_conn = key.data
                    try:
                        prot_conn.process_events(mask)
                    except Exception:
                        print(
                            "main: error: exception for",
                            f"{prot_conn.addr}:\n{traceback.format_exc()}",
                        )
                        prot_conn.close()
                # Check for a socket being monitored to continue.
                if not self.sel.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self.sel.close()

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


if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
curses_color = False

try:
    # Start connection to server
    game_client = GameClient(host, port)
    game_client.start()
    # Send a new request
    map, players, computers, flush_input, refresh_rate = get_user_request()

    game_state, colors = game_client.start_game(map, players, computers, flush_input, refresh_rate)

    if game_state == GameState.STARTED:
        stdscr = curses.initscr()
        if curses.has_colors():
            curses.start_color()
            curses_color = True

            for color in colors:
                curses.init_pair(color.get("number"), utils.parseColor(color.get("fg")), utils.parseColor(color.get("bg")))

    while game_state == GameState.STARTED:
        drawn_map, game_state, winner = game_client.query_game()
        print(repr(drawn_map))
        time.sleep(refresh_rate)

    print("\n\nGame ended!\n")

    if winner:
        print(winner + " WON!!!!")

except KeyboardInterrupt:
    sys.exit(1)