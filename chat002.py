# Chat
# Noah Kim, Haron Adbaru

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
TIME = "%I:%M %p"

# Function
def message(**info) -> dict:
    """Generate a message dictionary."""
    if info.get("time") is None:
        info["time"] = time.strftime(TIME)
    return info

def hidden(ip) -> str:
    """Hide the machine part of an ip address."""
    return ".".join(ip.split(".")[:2] + ["xxx",] * 2)

# Client
class Client:
    def create(self):
        """Build the graphical user interface of the application."""
        pass

# Server
class Handler:
    pass

class Server:
    pass
