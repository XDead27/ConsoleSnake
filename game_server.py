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

    global active_rooms
    global running_games            

    if action == "create_room":
        # Get all variables from the request
        name = value.get("name")
        map_name = value.get("map")
        computers = value.get("computers")
        flush_input = value.get("f_input")
        refresh = value.get("refresh")
        game_id = random.randint(99, 999)

        # Create a map instance
        #
        #   This way we can have access to specific options and previews
        m = __import__("Maps." + map_name)
        m = getattr(m, map_name)

        map_instance = getattr(m, map_name.capitalize())()

        # Create a new room with the specified parameters
        new_room = room.Room(game_id, name, map_name, map_instance, computers, flush_input, refresh)

        active_rooms[game_id] = new_room

        # Return the room_id in a new response
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

            response_action = "room_update"
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
    elif action == "update_room_options":
        room_id = value.get("room_id")
        wanted_room = active_rooms.get(room_id)

        if wanted_room:
            new_options = value.get("room_options")
            wanted_room.map_instance.setOptions(new_options)

            response_action = "room_update"
            response_value = {
                    "room_data": active_rooms.get(room_id).json_data()
                }
        else:
            response_action = "notice"
            response_value = {
                    "message": "Room does not exist!"
                }
    elif action == "room_query":
        room_id = value.get("room_id")
        wanted_room = active_rooms.get(room_id)

        if wanted_room:
            response_action = "room_update"
            response_value = {
                    "room_data": active_rooms.get(room_id).json_data()
                }
        else:
            response_action = "notice"
            response_value = {
                    "message": "Room does not exist!"
                }
    elif action == "leave_room":
        room_id = value.get("room_id")
        player_id = value.get("player_id")

        wanted_room = active_rooms.get(room_id)
        for idx in range(len(wanted_room.players)):
            if player_id == wanted_room.players[idx].get("id"):
                del wanted_room.players[idx]
                break

        response_action = "notice"
        response_value = {
                "message": "Successfully removed player!"
            }
    elif action == "start_game":
        room_id = value.get("room_id")
        instigator_id = value.get("player_id")
        room_to_start = active_rooms.get(room_id)

        if instigator_id == room_to_start.host.get("id"):
            map_instance = room_to_start.map_instance
            players = room_to_start.players
            computers = room_to_start.computers
            flush_input = room_to_start.f_input
            refresh = room_to_start.refresh_rate
            game_id = room_id

            new_game = game.Game(game_id, map_instance, players, computers, flush_input, refresh)

            new_game.start()
            room_to_start.game_state = 1

            running_games[game_id] = new_game

            response_action = "notice"
            response_value = {
                    "message": "Game started!"
                    }
        else:
            response_action = "notice"
            response_value = {
                    "message": "You are not the host!"
                }
    elif action == "get_game_vars":
        game_id = value.get("game_id")

        wanted_game = running_games.get(game_id)

        response_action = "notice"
        response_value = {
                "message": "Game vars sent!",
                "colors": wanted_game.getAllColors()
            }
    elif action == "query":
        game_id = value.get("game_id")
        wanted_game = running_games.get(game_id)
        drawn_map = []

        game_state = wanted_game.game_state
        drawn_map = wanted_game.field.drawnMap
        winner = wanted_game.game_winner
        score = wanted_game.getScores()

        response_action = "update"
        response_value = {
                "drawn_map": drawn_map,
                "game_state": game_state,
                "winner": winner,
                "score_data": score
            }

        if game_state == 2:
            # running_games.pop(game_id)
            active_rooms.get(game_id).game_state = 0

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
    elif action == "delete_room":
        room_id = value.get("room_id")
        instigator_id = value.get("player_id")

        # Shit security for now
        if instigator_id == active_rooms.get(room_id).host.get("id"):
            active_rooms.pop(room_id)

            response_action = "notice"
            response_value = {
                    "message": "Successfully deleted room!",
                    # Yes I am a ~Programmer~ how could you tell
                    "ok": True
                }
        else:
            response_action = "notice"
            response_value = {
                    "message": "You are not the host of the said room!"
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

host = '127.0.0.1'
port = 1403

if len(sys.argv) == 3:
    host, port = sys.argv[1], int(sys.argv[2])
elif len(sys.argv) != 1:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

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
