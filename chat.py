# Chat
# Noah Kim, Haron Adbaru

# For Africa!

# Import
import tkinter
import tkinter.scrolledtext
import tkinter.messagebox

import socketserver
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
def message(**values):
    return values

def hide(ip):
    return ".".join(ip.split(".")[:2] + ["xxx",] * 2)

# Class
# NOPE
