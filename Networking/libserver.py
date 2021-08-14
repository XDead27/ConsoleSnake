import sys
import selectors
import json
import io
import struct

def create_request(action, value, type="text/json", encoding="utf-8"):
    return dict(
        type=type,
        encoding=encoding,
        content=dict(action=action, value=value) if type == "text/json" else bytes(action + str(value), encoding="utf-8"),
    )

def _json_encode(obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

def _json_decode(json_bytes, encoding):
    tiow = io.TextIOWrapper(
        io.BytesIO(json_bytes), encoding=encoding, newline=""
    )
    obj = json.load(tiow)
    tiow.close()
    return obj


class Connection:
    def __init__(self, selector, sock, addr, request_handler):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.ack = 0
        self.request = None
        self.response = None
        self._request_handler = request_handler

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            raise RuntimeError("Resource temporarily unavailable.")
            # pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("\033[31m" + "sending" + "\033[0m", repr(self._send_buffer), "to", self.addr, "\n")
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Listen when the buffer has been drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.refresh_connection()
                    self._set_selector_events_mask("r")

    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
            "ack": self.ack
        }
        jsonheader_bytes = _json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()
        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.request is None:
                self.process_request()

    def write(self):
        if self._has_response:
            self.create_response()

        self._write()

        if not self._has_response:
            if not self._send_buffer:
                # Set selector to listen for read events, we're done writing.
                self._set_selector_events_mask("r")

    def close(self):
        print("\033[31m" + "closing connection to" + "\033[0m", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    # def place_response(self, response):
    # self.request = request
    # self._has_request = True
    # self._set_selector_events_mask("w")

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = _json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_request(self):
        self.ack = self.jsonheader["seq"]
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = _json_decode(data, encoding)
            print("\033[31m" + "received request" + "\033[0m", repr(self.request), "from", self.addr)
        else:
            # Binary or unknown content-type
            self.request = data
            print(
                f'received {self.jsonheader["content-type"]} request from',
                self.addr,
            )
        print(" ")
        # Set selector to listen for write events, we're done reading.
        self._has_response = True
        self.response = self._request_handler(self.request)
        self._set_selector_events_mask("w")


    def send_response(self, response):
        self.response = response
        self._has_response = True
        self._set_selector_events_mask("w")

    def create_response(self):
        content = self.response["content"]
        content_type = self.response["type"]
        content_encoding = self.response["encoding"]
        if content_type == "text/json":
            response = {
                "content_bytes": _json_encode(content, content_encoding),
                "content_type": content_type,
                "content_encoding": content_encoding,
            }
        else:
            response = {
                "content_bytes": content,
                "content_type": content_type,
                "content_encoding": content_encoding,
            }
        message = self._create_message(**response)
        self._send_buffer += message
        self._has_response = False

    # def create_response(self):
    #     if self.jsonheader["content-type"] == "text/json":
    #         response = self._request_handler(self.request)
    #     message = self._create_message(**response)
    #     self._send_buffer += message
    #     self._has_response = False

    def refresh_connection(self):
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self._has_response = False
        print("\n===============================\n")