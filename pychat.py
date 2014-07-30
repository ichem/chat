# PyChat
# Noah K, Haron A

# Import
import logging
import time
import socket

# Logging
from logging import FATAL, CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATEFMT = "%m/%d/%y %I:%M:%S %p"
LEVEL = NOTSET
logging.basicConfig(format=FORMAT, datefmt=DATEFMT, level=LEVEL)

# Utility
def name(obj) -> str:
    """Return the name of an object's type."""
    return type(obj).__name__

def censor(ip, parts=2) -> str:
    """Censor an ip for privacy, blocking the specified number of parts."""
    return ".".join(ip.split(".")[:-parts] + parts * ["***"])

# Message
JOIN = "%s joined"
EXIT = "%s exited"
CHAT = {"format": "[%(datefmt)s] %(name)s: %(message)s", "datefmt": "%I:%M %p"}
INFO = {"format": "[%(datefmt)s] %(message)s", "datefmt": "%I:%M %p"}
EMPTY = {"format": "%(message)s"}

def new(**info) -> dict:
    """Convenience function for creating new messages."""
    return info

def encode(message) -> bytes:
    """Convenience function for pickling messages."""
    return pickle.dumps(message)

def decode(message) -> dict:
    """Convenience function for unpickling messages."""
    return pickle.loads(message)

def string(template, message) -> str:
    """Convenience function for formatting messages as strings."""
    if template.get("datefmt"):
        message["datefmt"] = time.strftime(template["datefmt"], message["time"])
    return template["format"] % message

# Server
IP = socket.gethostbyname(socket.gethostname())
PORT = 50000
ADDRESS = (IP, PORT)
SIZE = 1024
COMMAND = "/"

class Handler:
    """Handler class for interacting with connected clients. Runs the sending
    and receiving of messages and passes them directly to/from the server."""

    # Magic
    def __init__(self, socket, address, server):
        """Initialize a new handler based on a socket connection, address, and
        chat server."""
        self.socket = socket
        self.address = address
        self.server = server
        self.info = dict()
        self.active = False
        logging.log(DEBUG, "%s: initialized", repr(self))

    def __repr__(self):
        """Return repr(handler)."""
        return "Handler<%s>" % self.address[0]

    # Function
    def give(self, message):
        """Give a message to the parent server."""
        self.server.messages.put(message)

    def send(self, message):
        """Send a message to the connected client."""
        data = encode(message)
        self.socket.send(data)

    # Loop
    def receive(self):
        """Receive messages from the connected client. Also handles connection
        and disconnection from the server."""
        logging.log(DEBUG, "%s: receive loop started", repr(self))
        data = self.socket.recv(SIZE)
        message = decode(data)
        self.info = message.copy()
        message = new(
            time=time.time(), template=INFO, message=JOIN % self.info["name"])
        self.give(message)
        logging.log(DEBUG, "%s: joined", repr(self))
        while self.active:
            try:
                data = self.socket.recv(SIZE)
                message = decode(data)
                message["handler"] = self
                self.give(message)
            except Exception as e:
                if self.active:
                    logging.log(
                        ERROR, "%s: %s in receive", repr(self), name(e))
                    self.shutdown()
        message = new(
            time=time.time(), template=INFO, message=EXIT % self.info["name"])
        self.give(message)
        logging.log(DEBUG, "%s: exited", repr(self))
        logging.log(DEBUG, "%s: receive loop finished", repr(self))

    # Main
    def activate(self):
        """Activate the handler."""
        if self.active:
            logging.log(WARNING, "%s: already activated", repr(self))
            return
        self.active = True
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()
        self.server.handlers.append(self)
        logging.log(INFO, "%s: activated", repr(self))

    def shutdown(self):
        """Shut down the handler."""
        if self.active:
            logging.log(WARNING, "%s: already shut down", repr(self))
            return
        self.active = True
        self.server.handlers.remove(self)
        logging.log(INFO, "%s: shut down", repr(self))

class Server:
    """Chat server that utilizes handlers to interact with connected clients
    via sockets."""

    # Magic
    def __init__(self, address):
        """Initialize a new chat server on an address."""
        self.address = address
        self.messages = queue.Queue()
        self.handlers = list()
        self.active = False
        logging.log(DEBUG, "%s: initialized", repr(self))

    def __repr__(self):
        """Return repr(server)."""
        return "Server<%s>" % self.address[0]

    # Function
    def send(self, message, handler=None):
        """Broadcast a message or send it to a specific handler."""
        if handler:
            handler.send(message)
        else:
            for handler in self.handlers:
                handler.send(message)

    # Loop
    def listen(self):
        """Listen for incoming connections from possible clients."""        
        logging.log(DEBUG, "%s: listen loop started", repr(self))
        while self.active:
            try:
                socket, address = self.socket.accept()
                handler = Handler(socket, address, self)
                handler.activate()
            except Exception as e:
                if self.active:
                    logging.log(ERROR, "%s: %s in listen", repr(self), name(e))

    def serve(self):
        """Main server loop handles incoming messages and handles them."""
        logging.log(DEBUG, "%s: serve loop started", repr(self))
        while self.active:
            try:
                while not self.messages.empty():
                    message = self.messages.get()
                    formatted = string(message["format"], message)
                    message = new(message=formatted)
                    self.send(message)
            except Exception as e:
                if self.active:
                    logging.log(ERROR, "%s: %s in serve", repr(self), name(e))

    def activate(self):
        """Activate the handler."""
        if self.active:
            logging.log(WARNING, "%s: already actvated", repr(self))
        try:
            self.socket = socket.socket()
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.address)
            self.socket.listen(5)
            logging.log(DEBUG, "%s: bound" % repr(self))
        except OSError as e:
            logging.log(FATAL, "%s: could not bind" % repr(self))
            return
        logging.log(DEBUG, "%s: initialized" % repr(self))
