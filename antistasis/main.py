# --------------------------------------------------------------

# PROGRAM DATA
gameTitle = "Antistasis"
gameVersion = "0.0.1"

# --------------------------------------------------------------

# PACKAGE IMPORT

import os
import sys
import time
import math
import random
import subprocess
import numpy as np #2.1.1
import pandas as pd #2.2.2
import pygame #2.6.1
from pygame.locals import *
import pyglet #2.0.20

from graphics import *
from ui import *
from simulation import *

# --------------------------------------------------------------

# FUNCTIONS & CLASSES

# Write to stdout (alternative to print)
def write_stdout(text):
    sys.stdout.write(str(text))
    sys.stdout.write("\n")

# --------------------------------------------------------------

# INITIALIZATION

def run():

    # Initialize
    pygame.init()

    # Print game info
    introString = gameTitle.upper() + " " + gameVersion
    separatorString = "=" * len(introString)

    write_stdout(separatorString)
    write_stdout(introString)
    write_stdout(separatorString)

    # Load all graphics in resources folder
    graphics = Graphics()

    # Set up the drawing window, get reference to screen, set window title/caption
    mainGameWindow = GameWindow(True, graphics)
    screen = mainGameWindow.screen
    mainGameWindow.set_caption(introString)
    mainGameWindow.set_icon(graphics.data['icon'])

    # Initialize mouse object
    mouse = Mouse_Data()

    # Initialize map object
    map = GameMap(mainGameWindow, graphics, mouse, 32)

    # Font for on-screen text
    font = pygame.font.SysFont('simsunextb.ttf', 32)
    contourFont = pygame.font.Font('resources/fonts/unispace.ttf', 14)
    pokeFont = pygame.font.Font('resources/fonts/PokemonGb-RAeo.ttf', 14)
    textBackdropColor = None

    #~~~~~~~~~~~
    # Game loop
    #~~~~~~~~~~~

    running = True
    mouseDown = False
    readout = True
    readoutAdv = True
    limit_fps = True
    timer = Timer(60.0, 10)
    simulate = False
    simSpeed = 1
    simTicks = 60.0
    hours = 0
    while running:

        # Increment ticks
        if simulate:
            timer.increment_tick()
            if timer.tick == simTicks:
                hours += 1
                map.sunAzimuth += 15
                if map.sunAzimuth >= 360:
                    map.sunAzimuth -= 360
                map.reset_suntiles()
                map.heat_calcs()
                map.gas_calcs()
                #map.calc_velocity()
                map.reset_tiles()
                timer.reset_tick()  
            
        # Start timing process
        timer.start_timer()
        
        # Get mouse position
        mouse.update()

        # Look at every event
        for event in pygame.event.get():
        
            # Did the user hit a key?
            if event.type == KEYDOWN:
            
                # Quit on escape
                if event.key == K_ESCAPE:
                    running = False
                    
                # Toggle stats (FPS, coords, etc)
                if event.key == K_q:
                    if readout:
                        readout = False
                    else:
                        readout = True
                        
                # Raise sea level
                if event.key == K_w:
                    map.seaLevel += 100
                    map.reset_tiles()

                # Lower sea level
                if event.key == K_e:
                    map.seaLevel -= 100
                    map.reset_tiles()

                # Toggle FPS cap
                if event.key == K_x:
                    if limit_fps:
                        limit_fps = False
                    else:
                        limit_fps = True

                # Toggle wind arrows
                if event.key == K_v:
                    if map.windArrows:
                        map.windArrows = False
                    else:
                        map.windArrows = True
                    map.reset_tiles()
                    
                # Toggle sunlight
                if event.key == K_s:
                    if map.displaySun:
                        map.displaySun = False
                    else:
                        map.displaySun = True
                    map.reset_tiles()
                    
                # Toggle sunlight
                if event.key == K_COMMA:
                    map.greenhouse -= 0.05
                    
                # Toggle sunlight
                if event.key == K_PERIOD:
                    map.greenhouse += 0.05
                    
                # Adjust sim speed/pause
                if event.key == K_SPACE:
                    timer.reset_tick() 
                    if simulate and simSpeed == 5:
                        simulate = False
                    elif simulate and simSpeed < 5:
                        simSpeed += 1
                    else:
                        simulate = True
                        simSpeed = 1
                    if simSpeed == 1:
                        simTicks = 60.0
                        simSpeedFactor = "(1x)"
                    elif simSpeed == 2:
                        simTicks = 30.0
                        simSpeedFactor = "(2x)"
                    elif simSpeed == 3:
                        simTicks = 15.0
                        simSpeedFactor = "(4x)"
                    elif simSpeed == 4:
                        simTicks = 5.0     
                        simSpeedFactor = "(12x)"
                    elif simSpeed == 5:
                        simTicks = 1.0     
                        simSpeedFactor = "(60x)"                    
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                map.click_and_drag_init()
                mouseDown = True

            elif event.type == pygame.MOUSEBUTTONUP:
                mouseDown = False

            elif event.type == pygame.MOUSEWHEEL:
                map.zoom(event.y)

            # Did the user click the window close button? If so, stop the loop.
            elif event.type == QUIT:
                running = False        

        # Pressed keys
        keys = pygame.key.get_pressed()

        # Mouse click & drag mechanic        
        if mouseDown:
            map.click_and_drag_update()

        # Reset screen center
        if keys[pygame.K_z]:
            map.reset_view()

        if keys[pygame.K_1]:
            map.displayMode = "Surface"
            map.unit = None
            map.reset_tiles()
            
        if keys[pygame.K_2]:
            map.displayMode = "Elevation"
            map.unit = "ft"
            map.reset_tiles()
            
        if keys[pygame.K_3]:
            map.displayMode = "Elevation Ground-Only"
            map.unit = "ft"
            map.reset_tiles()
            
        if keys[pygame.K_4]:
            map.displayMode = "Surface Temperature"
            map.unit = "°F"
            map.reset_tiles()
            
        if keys[pygame.K_5]:
            map.displayMode = "Air Temperature"
            map.unit = "°F"
            map.reset_tiles()
            
        if keys[pygame.K_6]:
            map.displayMode = "Air Pressure"
            map.unit = "psi"
            map.reset_tiles()
            
        if keys[pygame.K_7]:
            map.displayMode = "Air Density"
            map.unit = "lb/ft^3"
            map.reset_tiles()
            
        if keys[pygame.K_8]:
            map.displayMode = "Wind Speed"
            map.unit = "mph"
            map.reset_tiles()
            
        # Fill the background with color
        screen.fill(backdropColor)
             
        # Generate map and blit
        mapSurface, origin = map.get_map()
        screen.blit(mapSurface, origin)
        
        # Display sunlit area if enabled
        if map.displaySun:
            sunSurface, origin = map.get_sun_map()
            screen.blit(sunSurface, origin)
        
        # Plot contour levels
        if map.contourEnabled:
            map.contour.create(map.contourMin, map.contourMax, map.unit, contourFont)

        # Update mouse coordinates
        mouse.update()

        # Toggle display of run/simulation stats
        if readout:

            # Run Stats
            if readoutAdv:

                # Calculate and display FPS
                #fps = timer.calc_fPS()
                #fpsString = "FPS = " + str(round(fps, 3))
                #fpsText = pokeFont.render(fpsString, True, textColor, textBackdropColor)
                #screen.blit(fpsText, (10, 10))

                # Display mouse coordinates
                mousePosText = pokeFont.render(str(mouse.pos), True, textColor, textBackdropColor)
                screen.blit(mousePosText, (10, 36))
            
            # Display current map view mode
            displayModeText = pokeFont.render("Mode: " + str(map.displayMode), True, textColor, textBackdropColor)
            screen.blit(displayModeText, (10, 62))
            
            if simulate:
                runningText = pokeFont.render("Simulation Running " + simSpeedFactor, True, textColor, textBackdropColor)
            else:
                runningText = pokeFont.render("Simulation Paused (0x)", True, textColor, textBackdropColor)
            screen.blit(runningText, (10, 88))
            
            displayGreenhouseText = pokeFont.render("Greenhouse Effect: " + str(round(map.greenhouse, 2)), True, textColor, textBackdropColor)
            screen.blit(displayGreenhouseText, (10, 114))
            
            # Display time values
            hoursRem = hours % 24.0
            days = (hours - hoursRem) / 24.0
            daysRem = days % 365
            years = (days - daysRem) / 365
            displayTimeText = pokeFont.render(str(round(years)) + " years, " +str(round(daysRem)) + " days, " + str(round(hoursRem)) + " hrs", True, textColor, textBackdropColor)
            screen.blit(displayTimeText, (10, 140))

        # Flip the display
        pygame.display.flip()

        # Limit fps to 60
        if limit_fps:
            elapsedTime = timer.get_elapsed()
            if elapsedTime < 1.0/60.0:
                remainingTime = 1.0/60.0 - elapsedTime
                time.sleep(remainingTime)

        # Tick timer
        timer.record_time()

    # QUITTING ROUTINE
    pygame.quit()


if __name__ == "__main__":
    run()