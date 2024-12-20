import os
import sys
import time
import pygame

# Object to hold/update data about mouse
class Mouse_Data:

    # Initialize at origin
    def __init__(self):
        self.pos = (0, 0)
        self.posHold = None
        
    # Update mouse position
    def update(self):
        self.pos = pygame.mouse.get_pos()
        

# Timer class for tracking FPS
class Timer:

    # Setup timer based on target FPS (default 60)
    def __init__(self, targetRate=60.0, samples=10):
        self.samples = samples
        self.nsConv = 1.0*10.0**9
        self.targetSpeed = 1.0/targetRate
        self.timeList = [self.targetSpeed]*self.samples
        self.timeRec = 0
        self.tick = 0
        self.fps = 0
        
    # Record initial time, meant to be run at beginning of game loop
    def start_timer(self):
        self.timeRec = time.perf_counter_ns()
        
    # Calculate elapsed time, meant to be run at end of game loop
    # Appends time to end of list for averaging FPS
    def record_time(self):
        self.elapsed = (time.perf_counter_ns() - self.timeRec) / self.nsConv
        self.timeList.append(self.elapsed)
        self.timeList = self.timeList[-self.samples:]
        
    # Get elapsed time without recording it
    def get_elapsed(self):
        self.elapsed = (time.perf_counter_ns() - self.timeRec) / self.nsConv
        return self.elapsed
        
    # Simple increment of tick counter
    def increment_tick(self):
        self.tick += 1
        
    # Simple increment of tick counter
    def reset_tick(self):
        self.tick = 0
        
    # Runs average of timer list to get FPS
    def calc_fps(self):
        averageTime = sum(self.timeList)/self.samples
        self.fps = 1.0/averageTime
        return self.fps
