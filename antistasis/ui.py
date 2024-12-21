import os
import sys
import time
import pygame
import datetime

currentDirectory = os.getcwd()
parentDirectory = os.path.dirname(currentDirectory)
logFilePath = os.path.join(parentDirectory, "game.log")

def get_time_string():
    """Writes current time a string of format:
       MM/DD/YYYY H:M:S"""
    currentTime = datetime.datetime.now()
    return currentTime.strftime("%m/%d/%Y %H:%M:%S")

def log(string, log=True):
    """Writes a string to stdout and .log file."""
    sys.stdout.write(f"{string}\n")
    if log:
        with open(logFilePath, "a+") as logFile:
            string = get_time_string() + ": " + string + "\n"
            logFile.write(string)
