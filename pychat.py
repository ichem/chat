# PyChat
# Noah K, Haron A

# Import
import logging
import pickle
import time
import socket
import threading
import queue
import tkinter
import tkinter.scrolledtext
import tkinter.messagebox
import time
import re

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
CLIENT_MESSAGE = "[%I:%M %p] *%%(name)s*: %%(message)s"
SERVER_MESSAGE = "[%I:%M %p] %%(message)s"

def Message(**data) -> dict:
    """Convenience function for generating messages. Also generates creation
    time of the message."""
    return data

def encode(message) -> bytes:
    """Convenience function for encoding messages for sending."""
    return pickle.dumps(message)

def decode(message) -> dict:
    """Convenience function for decoding messages for receiving."""
    return pickle.loads(message)

# Server
try: IP, PORT = socket.gethostbyname(socket.gethostname()), 50000
except: logging.log(WARNING, "could not determine address")
SIZE = 1024
COMMAND = "/"
CLIENT = "client"
SERVER = "server"

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
        self.active = False
        self.name = ""
        logging.log(DEBUG, "%s: initialized" % repr(self))

    def __repr__(self):
        """Return repr(handler)."""
        return "Handler<%s>" % self.address[0]

    # Single
    def send(self, message):
        """Send a message to the connected client."""
        data = encode(message)
        self.socket.send(data)

    # Loop
    def recieve(self):
        """Loop receive data from the connected client."""
        logging.log(DEBUG, "%s: recieve loop started" % repr(self))
        while self.active:
            try:
                data = self.socket.recv(SIZE)
                message = decode(data)
                message["handler"] = self
                self.server.messages.put(message)
            except Exception as e:
                if self.active:
                    logging.log(ERROR, "%s: %s in recieve" % (
                        repr(self), type(e).__name__))
                    self.shutdown()

    # Main
    def activate(self):
        """Activate the handler."""
        if self.active:
            logging.log(WARNING, "%s: already activated" % repr(self))
            return
        self.active = True
        data = self.socket.recv(SIZE)
        message = decode(data)
        self.name = message["name"]
        new = Message(
            type=SERVER, message="*%s joined*" % self.name,
            time=time.time(), handler=self)
        time.sleep(0.01)
        self.server.messages.put(new)
        self.recieve_thread = threading.Thread(target=self.recieve)
        self.recieve_thread.start()
        self.server.handlers.append(self)
        logging.log(INFO, "%s: activated" % repr(self))

    def shutdown(self):
        """Shut down the handler."""
        if not self.active:
            logging.log(WARNING, "%s: already shut down" % repr(self))
            return            
        self.active = False
        new = Message(
            type=SERVER, message="*%s quit*" % self.name,
            time=time.time(), handler=self)
        self.server.messages.put(new)
        self.server.handlers.remove(self)
        logging.log(INFO, "%s: shut down" % repr(self))

class Server:
    """Chat server that utilizes handlers to interact with the connected
    clients via sockets."""

    # Magic
    def __init__(self, address):
        """Initialize a new chat server on an address."""
        self.address = address
        self.messages = queue.Queue()
        self.handlers = list()
        self.active = False
        self.failed = False
        try:
            self.socket = socket.socket()
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.address)
            self.socket.listen(5)
            logging.log(DEBUG, "%s: bound" % repr(self))
        except OSError as e:
            logging.log(FATAL, "%s: could not bind" % repr(self))
            self.failed = True
        logging.log(DEBUG, "%s: initialized" % repr(self))

    def __repr__(self):
        """Return repr(server)."""
        return "Server<%s>" % self.address[0]

    # Single
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
        logging.log(DEBUG, "%s: listen loop started" % repr(self))
        while self.active:
            try:
                socket, address = self.socket.accept()
                handler = Handler(socket, address, self)
                handler.activate()
            except Exception as e:
                if self.active:
                    logging.log(ERROR, "%s: %s in listen" % (
                        repr(self), type(e).__name__))
                
    def serve(self):
        """Main server loop handles incoming messages and handles them."""
        logging.log(DEBUG, "%s: serve loop started" % repr(self))
        while self.active:
            try:
                while not self.messages.empty():
                    message = self.messages.get()
                    if message["message"].startswith(COMMAND):
                        if message["message"] == COMMAND + "join":
                            new = Message(
                                type=SERVER,
                                message="*%s joined*" % message["name"],
                                time=message["time"])
                            self.send(new)
                        elif message["message"] == COMMAND + "quit":
                            new = Message(
                                type=SERVER,
                                message="*%s quit*" % message["name"],
                                time=message.time())
                            self.send(new)
                        return
                    message.pop("handler") # Can't be pickled
                    self.send(message)
            except Exception as e:
                if self.active:
                    logging.log(ERROR, "%s: %s in serve" % (
                        repr(self), type(e).__name__))

    # Main
    def activate(self):
        """Activate the handler."""
        if self.failed:
            logging.log(ERROR, "%s: failed to activate" % repr(self))
            return
        if self.active:
            logging.log(ERROR, "%s: already activated" % repr(self))
            return
        self.active = True
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
        logging.log(INFO, "%s: activated" % repr(self))
        try:
            logging.log(INFO, "%s: type ctrl-c to shut down" % repr(self))
            self.serve()
        except KeyboardInterrupt:
            logging.log(INFO, "%s: received ctrl-c" % repr(self))
            self.shutdown()

    def shutdown(self):
        """Server shut down."""
        if not self.active:
            logging.log(ERROR, "%s: already shut down" % repr(self))
        self.active = False
        message = Message(
            type=SERVER, message=COMMAND + "shutdown", time=time.time())
        self.send(message)
        for handler in self.handlers:
            handler.shutdown()
        self.socket.close()
        logging.log(INFO, "%s: shut down" % repr(self))

def server(address=("127.0.0.1", 50000)):
    server = Server(address)
    server.activate()

# Client
ESCAPE_RE = r"(?P<escape>\\(.))"
BOLD_RE = r"(?P<bold>\*([^\*]+)\*)"
ITALICS_RE = r"(?P<italics>_([^_]+)_)"
COMPILED_RE = "|".join((ESCAPE_RE, BOLD_RE, ITALICS_RE))

class Client:
    """Chat client that interacts with the chat server via sockets."""

    # Magic
    def __init__(self, address, name):
        """Initialize a new, named client connecting to a server address."""
        self.address = address
        self.name = name
        self.messages = queue.Queue()
        self.active = False
        self.failed = False
        try:
            self.socket = socket.socket()
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.connect(self.address)
            logging.log(DEBUG, "%s: bound" % repr(self))
        except OSError as e:
            logging.log(FATAL, "%s: could not connect" % repr(self))
            self.failed = True
        logging.log(DEBUG, "%s: initialized" % repr(self))

    def __repr__(self):
        """Return repr(self)."""
        return "Client<%s>" % self.address[0]

    # Single
    def send(self, message):
        """Send a message to the connected server."""
        data = encode(message)
        self.socket.send(data)

    # Graphical
    def build(self):
        """Build the graphical interface."""
        self.root = tkinter.Tk()
        self.root.title("Chat")
        self.text = tkinter.scrolledtext.ScrolledText(
            self.root, bd=1, width=40, relief="sunken",
            state="disabled", font=("Verdana", 0))
        self.text.pack(fill="both", expand=2)
        self.text.config(height=30)
        self.entry = tkinter.Text(
            self.root, bd=1, width=40, height=3, relief="sunken",
            highlightcolor="white", font=("Verdana", 0))
        self.entry.pack(fill="x")
        logging.log(DEBUG, "%s: built" % repr(self))
        self.entry.bind("<Return>", self.input)
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.update()
        self.root.mainloop()

    def unbuild(self):
        """Un-build the graphical interface."""
        self.root.quit()
        self.root.destroy()
        logging.log(DEBUG, "%s: unbuilt" % repr(self))

    def input(self, event=None):
        """Get input from graphical interface."""
        if not event.state:
            text = self.entry.get("1.0", "end-1c") # -1c for trailing \n
            self.entry.delete("1.0", "end")
            message = Message(
                name=self.name, type=CLIENT, message=text, time=time.time())
            self.send(message)
            return "break"

    def print(self, string, end="\n"):
        """Print a string to the graphical interface."""
        self.text.config(state="normal")
        start = self.text.index("end")        
        self.text.insert("end", string + end)
        self.text.config(state="disabled")

    def clear(self):
        """Clear the entire graphical interface."""
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    # Loop
    def receive(self):
        """Loop receive data from the connected client."""
        logging.log(DEBUG, "%s: recieve loop started" % repr(self))
        while self.active:
            try:
                data = self.socket.recv(SIZE)
                message = decode(data)
                self.messages.put(message)
            except Exception as e:
                logging.log(ERROR, "%s: %s in recieve" % (
                    repr(self), type(e).__name__))
                if self.active:
                    self.shutdown()

    def update(self):
        """Update the graphical interface with any new messages."""
        if not self.active:
            self.unbuild()
        while not self.messages.empty():
            message = self.messages.get()
            MESSAGE = CLIENT_MESSAGE
            if message.get("type") == SERVER:
                if message["message"] == COMMAND + "shutdown":
                    logging.log(FATAL, "%s: server shut down" % repr(self))
                    self.shutdown()
                    return
                else:
                    MESSAGE = SERVER_MESSAGE
            time_ = time.localtime(message["time"])
            message_ = time.strftime(MESSAGE, time_) % message
            self.print(message_)
        self.root.after(50, self.update)
    
    # Main       
    def activate(self):
        """Activate the client."""        
        if self.failed:
            logging.log(ERROR, "%s: failed to activate" % repr(self))
            return
        if self.active:
            logging.log(ERROR, "%s: already activated" % repr(self))
            return
        self.active = True
        message = Message(
            name=self.name, type=CLIENT, message="/join", time=time.time())
        self.send(message)
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()
        logging.log(DEBUG, "%s: update loop started" % repr(self))
        logging.log(DEBUG, "%s: activated" % repr(self))
        self.build()
        
    def shutdown(self):
        """Shut down the client."""
        if not self.active:
            logging.log(WARNING, "%s: already shut down" % repr(self))
            return
        self.active = False
        message = Message(
            name=self.name, type=CLIENT, message="/quit", time=time.time())
        self.send(message)
        try:
            self.socket.shutdown(0)
        except:
            logging.log(FATAL, "%s: server shut down" % repr(self))
        logging.log(DEBUG, "%s: shut down" % repr(self))

def client(address=("127.0.0.1", 50000), name="John Doe"):
    client = Client(address, name)
    client.activate()

