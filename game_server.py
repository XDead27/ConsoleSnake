#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import random, threading

import Networking.libserver as libserver
import game
import Resources.room as room

sel = selectors.DefaultSelector()

active_rooms = {}
running_games = {}

def handle_request(content):
    action = content.get("action")
    value = content.get("value")

    response_action = "notice"
    response_value = ""
    response_type = "text/json"
    response_encoding = "utf-8"
    if action == "create_room":
        name = value.get("name")
        map = value.get("map")
        computers = value.get("computers")
        flush_input = value.get("f_input")
        refresh = value.get("refresh")
        game_id = random.randint(99, 999)

        new_room = room.Room(game_id, name, map, computers, flush_input, refresh)

        global active_rooms
        active_rooms[game_id] = new_room

        response_action = "notice"
        response_value = {
                "message": "Room created!",
                "room_id": game_id
            }
    elif action == "join_room":
        room_id = value.get("room_id")
        player_settings = value.get("settings")
        wanted_room = active_rooms.get(room_id)

        if wanted_room is not None:
            player_id = wanted_room.insert_player(player_settings)

            response_action = "notice"
            response_value = {
                    "message": "Succesfully added player to room!",
                    "player_id": player_id,
                    "room_data": active_rooms.get(room_id).json_data()
                }
        else:
            response_action = "notice"
            response_value = {
                    "message": "Room not found!"
                }
    elif action == "start_game":
        room_id = value.get("room_id")
        room_to_start = active_rooms.get(room_id)
        map = room_to_start.map
        players = room_to_start.players
        computers = room_to_start.computers
        flush_input = room_to_start.f_input
        refresh = room_to_start.refresh_rate
        game_id = room_id

        new_game = game.Game(game_id, map, players, computers, flush_input, refresh)

        new_game.start()

        global running_games            
        running_games[game_id] = new_game

        response_action = "notice"
        response_value = {
                "message": "Game started!",
                "game_id": game_id,
                "colors": new_game.getAllColors()
            }
    elif action == "query":
        game_id = value.get("game_id")
        drawn_map = []

        drawn_map = running_games[game_id].field.drawnMap
        game_state = running_games[game_id].game_state
        winner = running_games[game_id].game_winner

        response_action = "update"
        response_value = {
                "drawn_map": drawn_map,
                "game_state": game_state,
                "winner": winner
            }
    elif action == "input":
        game_id = value.get("game_id")
        player_id = value.get("player_id")
        input_to_register = value.get("input")

        wanted_game = running_games[game_id]
        try:
            if not input_to_register == None:
                wanted_game.placeInput(player_id, input_to_register)
        except Exception:
            message = "An error occured!"
        else:
            message = "Registered input!"

        response_action = "notice"
        response_value = {
                "message": message
            }
    elif action == "query_rooms":
        # Get room data from an array

        response_action = "room_list"
        response_value = {
                "room_data": [room.json_data() for room in active_rooms.values()]
            }
    else:
        print("\033[35m" + "Unknown action!" + "\033[0m")
        response_value = {"message": "not a recognized action!"}

    response = libserver.create_request(response_action, response_value, response_type, response_encoding)
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
        events = sel.select(timeout=None)
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
