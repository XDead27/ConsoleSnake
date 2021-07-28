#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback

import Networking.libclient as libclient

sel = selectors.DefaultSelector()


def create_request(action, value):
    return dict(
        type="text/json",
        encoding="utf-8",
        content=dict(action=action, value=value),
    )


def start_connection(host, port):
    addr = (host, port)
    print("starting connection to", addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    prot_conn = libclient.Connection(sel, sock, addr)
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
    request = create_request(action, value)
    prot_conn.place_request(request)
    while True:
        events = sel.select(timeout=1)
        if not events:
            # Send a new request
            action, value = get_user_request()
            request = create_request(action, value)
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
