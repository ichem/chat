# Chat
# Noah Kim, Haron Adbaru

# For Africa!

# Import
import tkinter
import tkinter.scrolledtext
import tkinter.messagebox

import socket
import threading

import pickle
import queue
import logging
import time

# Debug
from logging import FATAL, CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
logging.basicConfig(format="[%(asctime)s] %(levelname)-8s %(message)s",
                    datefmt="%H:%M:%S", level=NOTSET)

# Constant
RECV = 1024

# Function
def message(name=None, type=None, data=None, time=time.strftime("%I:%M %p")):
    return {
        "name": name,
        "type": type,
        "data": data,
        "time": time
    }

def hide(ip):
    return ".".join(ip.split(".")[:2] + ["xxx",] * 2)

# Class
class Client:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.messages = queue.Queue()
        self.alive = False
        logging.log(INFO, "%s initialized" % repr(self))

    def __repr__(self):
        return "Client<%s:%d>" % self.address

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.address)
            logging.log(INFO, "%s connected" % repr(self))            
        except OSError as e:
            logging.log(FATAL, "%s could not connect (%s)" % (
                repr(self), type))

    def send(self, message):
        data = pickle.dumps(message)
        self.socket.send(data)

    def recv(self):
        logging.log(INFO, "%s recv loop started" % repr(self))
        while self.alive:
            try:
                data = self.socket.recv(RECV)
                message = pickle.loads(data)
                self.messages.put(message)
            except Exception as e:
                logging.log(ERROR, "%s %s in recv loop" % (
                    repr(self), str(e)))
                self.shutdown()

    def update(self):
        while self.active:
            try:
                if not self.messages.empty():
                    message = self.messages.get()
                    self.handle(message)
            except Exception as e:
                logging.log(ERROR, "%s %s in update loop" % (
                    repr(self), type(e).__name__))

    def handle(self, message):
        print(message)

class Handler:
    def __init__(self, socket, address, server):
        self.socket = socket
        self.address = address
        self.server = server
        self.signature = {"handler": self}
        self.alive = False
        logging.log(INFO, "%s initialized" % repr(self))

    def __repr__(self):
        return "Handler<%s:%d>" % self.address

    def send(self, message):
        data = pickle.dumps(message)
        self.socket.send(data)
        logging.log(DEBUG, "%s sent message" % repr(self))

    def recv(self):
        logging.log(INFO, "%s recv loop started" % repr(self))
        while self.alive:
            try:
                data = self.socket.recv(RECV)
                message = pickle.loads(data)
                message.update(self.signature)
                self.server.messages.put(message)
            except Exception as e:
                logging.log(ERROR, "%s %s in recv loop" % (
                    repr(self), str(e)))
                self.shutdown()

    def activate(self):
        self.alive = True
        self.recv_thread = threading.Thread(target=self.recv)
        self.recv_thread.start()
        self.server.handlers.append(self)
        logging.log(INFO, "%s activated" % repr(self))

    def shutdown(self):
        self.alive = False
        self.socket.close()
        self.server.handlers.remove(self)
        logging.log(INFO, "%s shut down" % repr(self))

class Server:
    def __init__(self, address):
        self.address = address
        self.messages = queue.Queue()
        self.handlers = list()
        self.alive = False
        logging.log(INFO, "%s initialized" % repr(self))

    def __repr__(self):
        return "Server<%s:%d>" % self.address

    def bind(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.address)
            self.socket.listen(5)
            logging.log(INFO, "%s bound" % repr(self))            
        except OSError as e:
            logging.log(FATAL, "%s could not bind (%s)" % (
                repr(self), str(e)))

    def send(self, message, handler=None):
        if handler:
            handler.send(message)
        else:
            for handler in self.handlers:
                handler.send(message)

    def handle(self, mesage):
        print(message)

    def search(self):
        logging.log(INFO, "%s search loop started" % repr(self))
        while self.alive:
            try:
                socket, address = self.socket.accept()
                handler = Handler(socket, address, self)
                handler.activate()
            except Exception as e:
                logging.log(ERROR, "%s search loop: %s" % (
                    repr(self), type(e).__name__))

    def serve(self):
        logging.log(INFO, "%s serve loop started" % repr(self))
        while self.alive:
            try:
                if not self.messages.empty():
                    message = self.messages.get()
                    self.handle(message)
            except Exception as e:
                logging.log(ERROR, "%s serve loop: %s" % (
                    repr(self), type(e).__name__))
                
    def activate(self):
        self.alive = True
        self.bind()
        self.search_thread = threading.Thread(target=self.search)
        self.search_thread.start()
        logging.log(INFO, "%s activated" % repr(self))
        try:
            self.serve()
        except KeyboardInterrupt:
            logging.log(WARNING, "%s receiver KeyboardInterrupt" %
                        repr(self))
            self.shutdown()

    def shutdown(self):
        self.alive = False
        self.socket.close()
        logging.log(INFO, "%s shut down" % repr(self))
