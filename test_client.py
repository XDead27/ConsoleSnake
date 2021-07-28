#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import pickle, codecs
from art import text2art

import Networking.libclient as libclient

sel = selectors.DefaultSelector()

# Debug
def drawField(field):
    for x in range(field.height):
        to_print = ""
        for y in range(field.width):
            to_print += field.drawnMap[x][y][0]
        print(text2art(to_print, font='cjk'))


def process_response(content):
    action = content.get("action")
    value = content.get("value")

    if action == "notice":
        print("\033[31m" + "I have handled the response!"+ "\033[0m" +" Here is the notice:", value.get("message"))
        if value.get("input"):
            print("With input: ", value.get("input"))
    elif action == "update":
        field = pickle.loads(codecs.decode(value.encode(), "base64"))
        drawField(field)
    else:
        print("\033[31m" + "Response is not a notice! It is"+ "\033[0m", action)

def start_connection(host, port):
    addr = (host, port)
    print("starting connection to", addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    prot_conn = libclient.Connection(sel, sock, addr, response_handler=process_response)
    sel.register(sock, events, data=prot_conn)
    return prot_conn


def get_user_request():
    action = input("Action: ")
    value = input("Value: ")
    return action, value


if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
# Start connection to server
prot_conn = start_connection(host, port)

try:
    action, value = get_user_request()
    request = libclient.create_request(action, value)
    prot_conn.place_request(request)
    while True:
        events = sel.select(timeout=1)
        if not events:
            # Send a new request
            # action, value = get_user_request()
            action = "query"
            value = ""
            request = libclient.create_request(action, value)
            prot_conn.place_request(request)
        else:
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
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
