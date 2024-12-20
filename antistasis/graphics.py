import os
import sys
import pygame
from pygame.locals import *

# Colors (tuple)
backdropColor = (24, 24, 24)
textColor = (255, 255, 255)


# Write to stdout (alternative to print)
def write_stdout(text):
    sys.stdout.write(str(text))
    sys.stdout.write("\n")


# Rotate pygame image about center
# https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
def Rotate_Center(surf, image, pos, angle):

    # offset from pivot to center
    w, h = image.get_size()
    originPos = (w/2, h/2)
    image_rect = image.get_rect(topleft = (pos[0] - originPos[0], pos[1]-originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    
    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # roatetd image center
    rotated_image_center = (pos[0] - rotated_offset.x + w/2, pos[1] - rotated_offset.y + h/2)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

    # rotate and blit the image
    surf.blit(rotated_image, rotated_image_rect)


# Class representing main game window
class GameWindow:

    # Initialize window
    def __init__(self, defaultRes, graphics, resX=1920, resY=1080):
    
        # Get current screen info
        displayInfo = pygame.display.Info()
        self.screenSize = (displayInfo.current_w, displayInfo.current_h)
        flags = DOUBLEBUF

        # Set screen dimensions
        if defaultRes:
            self.x = resX
            self.y = resY
        else:
            self.x = screenSize[0]
            self.y = screenSize[1]
        self.area = self.x * self.y
        
        # Generate screen
        self.screen = pygame.display.set_mode([self.x, self.y], flags)
        
        # Print information to stdout
        write_stdout("Screen Resolution: " + str(self.screenSize[0]) + " x " + str(self.screenSize[1]) + " px")
        write_stdout("Window Resolution: " + str(self.x) + " x " + str(self.y) + " px")
        write_stdout("Window Total Area: " + str(self.area) + " px")

    def set_caption(self, string):
        pygame.display.set_caption(string)
        
    def set_icon(self, icon):
        pygame.display.set_icon(icon)

# Loads all graphics
class Graphics:
    
    # Pulls all image (.png) files from resources folder and loads as pygame image
    # Stores each in dictionary under filename (no extension) indices
    def __init__(self):
        self.directory = "resources/graphics"
        self.data = {}
        for file in os.listdir(self.directory):
            f = os.path.join(self.directory, file)
            splitExt = os.path.splitext(file)
            name = splitExt[0]
            ext = splitExt[1]
            if ext.lower() == '.png':
                img = pygame.image.load(f)
                self.data.update({name: img})


# Plots contour bars for specific views
class ContourBars:

    # Initialize
    def __init__(self, gameWindow, padding=10, spacing=21, valuesMax=6, decMax=3):
        self.gameWindow = gameWindow
        self.padding = padding
        self.spacing = spacing
        self.valuesMax = valuesMax
        self.decMax = decMax
        self.startValueY = self.gameWindow.y - 12*(spacing+2)
        self.barColors = ((255, 0, 220), (255, 0, 0), (255, 106, 0), (255, 216, 0), (182, 255, 0), \
                          (76, 255, 0), (0, 255, 144), (0, 255, 255), (0, 148, 255), (0, 38, 255), \
                          (87, 0, 127))
        self.backgroundColor = (25, 25, 25)
        self.unitColor = (255, 255, 255)
        #self.backgroundColor = None
        
    # Create contour bars and blit
    def create(self, min, max, units, font):
    
        # Full length of each display value (used to figure out how many spaces to pad strings with)
        fullLength = self.valuesMax + self.decMax + 1
    
        # Initial values
        currentPos = (10, self.startValueY)
        
        unitStringPadding = fullLength - len(str(units)) + 2
        unitString = "(" + str(units) + ")"
        contourText = font.render(unitString, True, self.unitColor, self.backgroundColor)
        self.gameWindow.screen.blit(contourText, currentPos)

        currentPos = (currentPos[0], currentPos[1] + self.spacing)
        currentValueUpper = float(max)
        
        # Max contour
        contourValueUpper = str(format(round(currentValueUpper, self.decMax), '.3f'))
        spacePad = fullLength - len(contourValueUpper) - 2
        contourValueUpper = " "*spacePad + contourValueUpper + " "*14
        
        contourString = ">=" + contourValueUpper
        contourText = font.render(contourString, True, self.barColors[0], self.backgroundColor)
        self.gameWindow.screen.blit(contourText, currentPos)
        
        # Initialize values to iterate
        contourInterval = (max - min) / 9.0
        currentValueLower = currentValueUpper - contourInterval
        
        for i in range(9):
            currentPos = (currentPos[0], currentPos[1] + self.spacing)
            
            contourValueUpper = format(round(currentValueUpper, self.decMax), '.3f')
            spacePad = fullLength - len(contourValueUpper) 
            contourValueUpper = " "*spacePad + contourValueUpper
            
            contourValueLower = format(round(currentValueLower, self.decMax), '.3f')
            spacePad = fullLength - len(contourValueLower) 
            contourValueLower = " "*spacePad + contourValueLower
            
            contourString = contourValueLower + " to " + contourValueUpper
            contourText = font.render(contourString, True, self.barColors[i+1], self.backgroundColor)
            self.gameWindow.screen.blit(contourText, currentPos)
            currentValueUpper -= contourInterval
            currentValueLower -= contourInterval
            
        # Min contour
        currentPos = (currentPos[0], currentPos[1] + self.spacing)
        
        currentValueLower = float(min)
        contourValueLower = format(round(currentValueLower, self.decMax), '.3f')
        spacePad = fullLength - len(contourValueLower) - 2
        contourValueLower = " "*spacePad + contourValueLower + " "*14
        
        contourString = "<=" + contourValueLower
        contourText = font.render(contourString, True, self.barColors[10], self.backgroundColor)
        self.gameWindow.screen.blit(contourText, currentPos)