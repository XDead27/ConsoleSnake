#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import random, threading

import Networking.libserver as libserver
import game

sel = selectors.DefaultSelector()

running_games = []

def handle_request(content):
    action = content.get("action")
    value = content.get("value")

    response_action = "notice"
    response_value = ""
    response_type = "text/json"
    response_encoding = "utf-8"
    if action == "start_game":
        map = value.get("map")
        players = value.get("players")
        computers = value.get("computers")
        flush_input = value.get("f_input")
        refresh = value.get("refresh")
        game_id = random.randint(99, 999)

        new_game = game.Game(game_id, map, players, computers, flush_input, refresh)

        new_game.start()

        global running_games            
        running_games.append(new_game)

        response_action = "notice"
        response_value = {
                "message": "Game started!",
                "game_id": game_id,
                "colors": new_game.getAllColors()
            }
    elif action == "input" or action == "query":
        game_id = value.get("game_id")
        drawn_map = []

        for g in running_games:
            if g.game_id == game_id:
                drawn_map = g.field.drawnMap
                game_state = g.game_state
                winner = g.game_winner
                break

        response_action = "update"
        response_value = {
                "drawn_map": drawn_map,
                "game_state": game_state,
                "winner": winner
            }
    else:
        print("\033[35m" + "Unknown action!" + "\033[0m")
        response_value = {"message": "not a recognized action!"}

    response = libserver.create_request(response_action, response_value, response_type, response_encoding)
    print(response)
    return response

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("\033[31m" + "accepted connection" + "\033[0m" + " from", addr, "\n")
    conn.setblocking(False)
    prot_conn = libserver.Connection(sel, conn, addr, handle_request)
    sel.register(conn, selectors.EVENT_READ, data=prot_conn)

if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                prot_conn = key.data
                try:
                    prot_conn.process_events(mask)
                except Exception:
                    print(
                        "\033[32m" + "main: error: exception for" + "\033[0m",
                        f"{prot_conn.addr}:\n{traceback.format_exc()}",
                    )
                    prot_conn.close()
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
