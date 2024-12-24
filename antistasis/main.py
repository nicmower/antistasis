# Standard libraries
import os
import sys
import time
import math
import random
import subprocess

# Third-party libraries
import numpy as np #2.1.1
import pandas as pd #2.2.2
import pygame #2.6.1
from pygame.locals import *
import pyglet #2.0.20

# Local imports
from graphics import *
from ui import *
from simulation import *
from __version__ import __title__ as gameTitle
from __version__ import __version__ as gameVersion

#############
# CONSTANTS #
#############

# Simulation
SEA_LEVEL_INCREMENT = 100   # ft
SUN_HOUR_ANGLE_INCREMENT = 15  # degrees
MAX_SUN_HOUR_ANGLE = 360       # degrees

SIM_TICK_DURATION = 1000    # ms
SIM_SPEED_LEVELS = [0, 1, 2, 5, 10, 25]

WORLD_SIZE = 35

# Pygame settings
EVENTS_USED = [pygame.KEYDOWN,          pygame.QUIT,        pygame.MOUSEBUTTONDOWN, \
               pygame.MOUSEBUTTONUP,    pygame.MOUSEWHEEL,  pygame.MOUSEMOTION]

#####################
# CLASSES/FUNCTIONS #
#####################

class Game:
    """Top-level class that holds all game objects."""
    
    def __init__(self):
        
        # Properties that inherit from elsewhere (other scripts, Pygame)
        self.graphics = None
        self.window = None
        self.screen = None
        self.map = None
        self.clock = None
        self.fonts = {}
        
        # Properties related to simulation speed/time
        self.running = True
        self.simulating = False
        self.lastTickTime = pygame.time.get_ticks()
        self.simSpeedIndex = 1
        self.hours = 0
        
        # Properties related to display
        self.readout = True
        
        # Properties related to controls
        self.mouseDown = False
        
        # Pygame keys and associated display mode name and units
        self.keyDisplayModes = {
        K_1: ('Surface', None),
        K_2: ('Elevation', 'ft'),
        K_3: ('Elevation, Land-Only', 'ft'),  
        K_4: ('Surface Temperature', '°F'),          
        K_5: ('Air Temperature', '°F'),        
        K_6: ('Air Pressure', 'psi'),        
        K_7: ('Air Density', 'lb/ft³'),        
        K_8: ('Wind Speed', 'mph'),        
        }
    
    def toggle_control(control):
        """Toggles a boolean control feature.
           E.g. can be used to switch map.displaySun to False."""
        control = not control
        log(f"{str(control)} is now {'enabled' if control else 'disabled'}.")
        self.map.reset_tiles()

    def raise_sea_level(self):
        """Passes user request to raise sea level to simulation core."""
        self.map.seaLevel += SEA_LEVEL_INCREMENT
        self.map.reset_tiles()
        
    def lower_sea_level(self):
        """Passes user request to raise sea level to simulation core."""
        self.map.seaLevel -= SEA_LEVEL_INCREMENT
        self.map.reset_tiles()

    def handle_keydown(self, event):
        """Handles a Pygame keydown event.
           Processes which key is pressed and triggers some other function."""

        # Quit on escape
        if event.key == K_ESCAPE:
            self.running = False
            
        # Reset view / center map
        elif event.key == K_z:
            self.map.reset_view()
            self.map.reset_tiles()
        
        # Switch display mode
        elif event.key in self.keyDisplayModes.keys():
            displayMode = self.keyDisplayModes[event.key]
            self.map.displayMode = displayMode[0]
            self.map.unit = displayMode[1]
            self.map.reset_tiles()
            
        # Toggle stats (FPS, coords, etc)
        if event.key == K_q:
            self.toggle_control(self.readout)
                
        # Raise sea level
        if event.key == K_w:
            self.raise_sea_level()

        # Lower sea level
        if event.key == K_e:
            self.lower_sea_level()

        # Toggle wind arrows
        if event.key == K_v:
            self.toggle_control(self.map.windArrows)
            
        # Toggle sunlight
        if event.key == K_s:
            self.toggle_control(self.map.displaySun)
            
        # Decrease greenhouse effect
        if event.key == K_LEFTBRACKET:
            self.map.decrease_greenhouse_effect()
            
        # Increase greenhouse effect
        if event.key == K_RIGHTBRACKET:
            self.map.increase_greenhouse_effect()
            
        # Adjust sim speed/pause
        if event.key == K_COMMA:
            self.decrease_sim_speed()                 
        if event.key == K_PERIOD:
            self.increase_sim_speed()         
        if event.key == K_SLASH:
            self.pause_sim()    

    def handle_events(self):
        """Handles Pygame events.
           Keydown events passed to handle_keydown."""

        # Loop through all events (filtered by EVENTS_USED)
        for event in pygame.event.get():

            # Keydowns passed to keydown handler function
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
                
            # Mouse currently only used to click-and-drag and zoom
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouseDown = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouseDown = False
            elif event.type == pygame.MOUSEMOTION:
                if self.mouseDown:
                    self.map.drag(event.rel)
            elif event.type == pygame.MOUSEWHEEL:
                self.map.zoom(event.y)
            
            # End game
            elif event.type == QUIT:
                self.running = False    
    
    def start_up(self):
        """Initializes Pygame, sets up game window/screen, creates game objects
           like mouse (for position/click tracking), graphics dictionary, and map."""
        
        # Log start time
        log("Starting up...")

        # Print game info
        titleAndVersion = gameTitle + " " + str(gameVersion)
        log(titleAndVersion)

        # Initialize pygame
        pygame.init()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed(EVENTS_USED)  
        log("Pygame started.")
        
        # Setup Pygame clock
        self.clock = pygame.time.Clock()

        # Load all graphics in resources folder
        self.graphics = Graphics()
        log("Graphics loaded.")

        # Set up the drawing window, set window title/caption, get reference to screen
        self.window = GameWindow(True, self.graphics)
        self.window.set_caption(titleAndVersion)
        self.window.set_icon(self.graphics.data['icon'])
        self.screen = self.window.screen
        log("Interface loaded.")

        # Initialize map object
        self.map = GameMap(self.window, self.graphics, WORLD_SIZE)
        log("Map initialized.")

        # Font for on-screen text
        self.fonts['default'] = pygame.font.SysFont('simsunextb.ttf', 32)
        self.fonts['contour'] = pygame.font.Font('resources/fonts/unispace.ttf', 14)
        self.fonts['pokemon'] = pygame.font.Font('resources/fonts/PokemonGb-RAeo.ttf', 14)
    
    @property
    def simSpeedFactor(self):
        """Property to get speed factor dynamically."""
        return SIM_SPEED_LEVELS[self.simSpeedIndex]
    
    def increase_sim_speed(self):
        """Adjust simulation speed up."""
        if self.simSpeedIndex < len(SIM_SPEED_LEVELS) - 1:
            self.simSpeedIndex += 1
        log(f"Game speed set to {self.simSpeedFactor}X")
        
    def decrease_sim_speed(self):
        """Adjust simulation speed down."""
        if self.simSpeedIndex > 0:
            self.simSpeedIndex -= 1
        log(f"Game speed set to {self.simSpeedFactor}X")
    
    def pause_sim(self):
        """Set simulation speed to zero."""
        self.simSpeedIndex = 0
        log(f"Game speed set to {self.simSpeedFactor}X")
    
    def simulate(self):
        """Run a single tick of the simulation.
           Corresponds to one real-world hour."""
        self.hours += 1
        self.map.sunHourAngle += SUN_HOUR_ANGLE_INCREMENT
        if self.map.sunHourAngle >= MAX_SUN_HOUR_ANGLE:
            self.map.sunHourAngle -= MAX_SUN_HOUR_ANGLE
        self.map.reset_suntiles()
        self.map.heat_calcs()
        self.map.smooth_temps()
        #self.map.gas_calcs()
        #map.calc_velocity()
        self.map.reset_tiles()
        
    def control_simulation(self):
        """Paces the simulation according to set speed."""
        
        # Skip simulation and rendering if game is paused   
        if self.simSpeedFactor > 0:
            
            # Calculate elapsed time since last tick
            currentTime = pygame.time.get_ticks()
            nextTickTime = self.lastTickTime + SIM_TICK_DURATION / self.simSpeedFactor

            # Check if enough time has passed for a simulation tick
            if currentTime >= nextTickTime:
                self.simulate()
                self.lastTickTime = currentTime
        
    def run(self):

        # Log start time
        log("Beginning game loop!")

        # Loop until game is quit
        while self.running:

            # Handle mouse/keyboard events
            self.handle_events()

            # Pace simulation according to speed setting
            self.control_simulation()    

            # Fill the background with color
            self.screen.fill(backdropColor)
                 
            # Generate map and blit
            mapSurface, origin = self.map.get_map()
            self.screen.blit(mapSurface, origin)
            
            # Display sunlit area if enabled
            if self.map.displaySun:
                sunSurface, origin = self.map.get_sun_map()
                self.screen.blit(sunSurface, origin)
            
            # Plot contour levels
            if self.map.contourEnabled:
                self.map.contour.create(self.map.contourMin, self.map.contourMax, self.map.unit, self.fonts['contour'])

            # Toggle display of run/simulation stats
            if self.readout:

                # Backdrop to enhance readout text clarity
                readoutBackdropBox = pygame.Surface((392, 166))
                readoutBackdropBox.set_alpha(150)
                readoutBackdropBox.fill((0, 0, 0))
                self.screen.blit(readoutBackdropBox, (0, 0))

                # Calculate and display FPS
                fps = self.clock.get_fps()
                fpsText = self.fonts['pokemon'].render(f"{fps:.1f}", True, textColor, textBackdropColor)
                self.screen.blit(fpsText, (10, 10))

                # Display mouse coordinates
                mousePosText = self.fonts['pokemon'].render(str(pygame.mouse.get_pos()), True, textColor, textBackdropColor)
                self.screen.blit(mousePosText, (10, 36))
                
                # Display current map view mode
                displayModeText = self.fonts['pokemon'].render("Mode: " + str(self.map.displayMode), True, textColor, textBackdropColor)
                self.screen.blit(displayModeText, (10, 62))
                
                if self.simSpeedFactor == 0:
                    runningText = self.fonts['pokemon'].render("Simulation Paused (0x)", True, textColor, textBackdropColor)
                else:
                    runningText = self.fonts['pokemon'].render("Simulation Running (" + str(self.simSpeedFactor) + "x)", True, textColor, textBackdropColor)
                self.screen.blit(runningText, (10, 88))
                
                displayGreenhouseText = self.fonts['pokemon'].render("Greenhouse Effect: " + str(round(self.map.greenhouse, 2)), True, textColor, textBackdropColor)
                self.screen.blit(displayGreenhouseText, (10, 114))
                
                # Display time values
                hoursRem = self.hours % 24.0
                days = (self.hours - hoursRem) / 24.0
                daysRem = days % 365
                years = (days - daysRem) / 365
                displayTimeText = self.fonts['pokemon'].render(str(round(years)) + " years, " +str(round(daysRem)) + " days, " + str(round(hoursRem)) + " hrs", True, textColor, textBackdropColor)
                self.screen.blit(displayTimeText, (10, 140))

            # Flip the display
            pygame.display.flip()
            self.clock.tick(60)

        # QUITTING ROUTINE
        pygame.quit()

    def launch(self):
        """Sequence of starting up & running game."""
        self.start_up()
        self.run()

if __name__ == "__main__":
    game = Game()
    game.launch()