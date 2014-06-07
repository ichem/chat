# Chat
# Noah Kim, Haron Adbaru

# Import
import logging

import re

import pickle
import time

# Logging
from logging import FATAL, CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATEFMT = "%m/%d/%y %I:%M:%S %p"
LEVEL = NOTSET

logging.basicConfig(format=FORMAT, datefmt=DATEFMT, level=LEVEL)

# Utility
def censor(ip, parts=2) -> str:
    """Censor an ip for privacy. Specify how much to censor with PARTS. No error
    checking implemented."""
    return ".".join(ip.split(".")[:-parts] + parts * ["***"])

# Message
def message(**data) -> dict:
    """Convenience function for generating messages. Also generates creation
    time of the message."""
    data["time"] = time.time()
    return data

def encode(message) -> bytes:
    """Convenience function for encoding messages for sending."""
    return pickle.dumps(message)

def decode(message) -> dict:
    """Convenience function for decoding messages for receiving."""
    return pickle.loads(message)
        
# Server
SIZE = 1024

class Handler:
    """Handler class for connected clients. Sends and receives messages, and
    interacts directly with the server."""

    # Magic
    def __init__(self, socket, address, server):
        """Initialize a new handler based on the socket connection and chat
        server."""
        self.socket = socket
        self.address = address
        self.server = server
        self.active = True
        logging.log(DEBUG, "%s: initialized" % repr(self))

    def __repr__(self):
        """Return repr(handler)."""
        return "Handler<%s>" % ":".join(self.address)

    # Single
    def send(self, message):
        """Send a message to the connected client."""
        data = encode(message)
        self.socket.send(data)
        logging.log(DEBUG, "%s: sent message" % repr(self))

    # Loop
    def recv(self):
        """Loop receive data from the connected client."""
        logging.log(DEBUG, "%s: recv loop started" % repr(self))
        while self.active:
            try:
                data = self.socket.recv(SIZE)
                message = decode(data)
                self.server.messages.put(message)
            except Exception as e:
                logging.log(ERROR, "%s: %s in recv loop" % (
                    repr(self), str(e)))
                self.shutdown()

    # Main
    def activate(self):
        """Activate the handler."""
        self.active = True
        self.recv_thread = threading.Thread(target=self.recv)
        self.recv_thread.start()
        self.server.handlers.append(self)
        logging.log(INFO, "%s: activated" % repr(self))

    def shutdown(self):
        """Shut down the handler."""
        self.active = False
        self.socket.close()
        self.server.handlers.remove(self)
        logging.log(INFO, "%s: shut down" % repr(self))
    
class Server:
    """Chat server that utilizes handlers to interact with the connected
    clients (via sockets)."""

    # Magic
    def __init__(self, address):
        """Initialize a new chat server on an address."""
        self.address = address
        self.messages = queue.Queue()
        self.handlers = list()
        self.active = False

        try:
            self.socket = socket.socket()
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.address)
            self.socket.listen(5)
            logging.log(DEBUG, "%s: bound" % repr(self))
        except OSError as e:
            logging.log(FATAL, "%s: could not bind (%s)" % (
                repr(self), repr(e)))
        
        logging.log(DEBUG, "%s: initialized" % repr(self))

    def __repr__(self):
        """Return repr(server)."""
        return "Server<%s>" % ":".join(self.address)

    # Single
    def handle(self, message):
        """Handle a message provided by the serv loop."""
        print(message)

    def send(self, message, handler=None):
        """Broadcast a message or send it to a specific handler."""
        if handler:
            handler.send(message)
        else:
            for handler in self.handlers:
                handler.send(message)

    # Loop
    def lstn(self):
        """Listen for incoming connections from possible clients."""        
        logging.log(DEBUG, "%s: lstn loop started" % repr(self))
        while self.active:
            try:
                socket, address = self.socket.accept()
                handler = Handler(socket, address, self)
                handler.activate()
            except Exception as e:
                logging.log(ERROR, "%s: %s in lstn loop" % (
                    repr(self), type(e).__name__))
                
    def serv(self):
        """Main server loop handles incoming messages and handles them."""
        logging.log(DEBUG, "%s: serv loop started" % repr(self))
        while self.active:
            try:
                if not self.messages.empty():
                    self.handle(self.messages.get())
            except Exception as e:
                logging.log(ERROR, "%s: %s in serv loop" % (
                    repr(self), type(e).__name__))

    # Main
    def activate(self):
        """Activate the handler."""
        self.active = True
        self.lstn_thread = threading.Thread(target=self.lstn)
        self.lstn_thread.start()
        logging.log(INFO, "%s: activated" % repr(self))
        try:
            logging.log(INFO, "%s: type ctrl-c to shut down")
            self.serve()
        except KeyboardInterrupt:
            logging.log(WARNING, "%s: received ctrl-c shut down signal" %
                        repr(self))
            self.shutdown()

    def shutdown(self):
        """Server shut down."""
        self.active = False
        self.socket.close()
        logging.log(INFO, "%s shut down" % repr(self))

# Client
class Client:
    pass

# Command
