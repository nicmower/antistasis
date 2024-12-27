# Standard libraries
import math
import random

# Local imports
from graphics import *
from ui import *

#############
# CONSTANTS #
#############

# Simulation/controls
GREENHOUSE_EFFECT_INCREMENT = 0.05

TIME_STEP = 1 # hrs

BASE_SUN_HEAT_FLUX = 1.2028 * 10**10    # BTU/hr per square mile from sun before albedo and latitude calcs

HEAT_RATIO_AIR = 0.23           # default/initial percent of sun's radiation absorbed by atmosphere

RADIATION_RATIO_AIR_TO_SURFACE = 0.5

SURFACE_RADIATION_ABSORPTION_AIR = 0.8

REFLECTION_RATIO_SURFACE_TO_AIR = 0.2

STEFAN_BOLTZMANN_CONSTANT = 0.1714      # BTU/(hr*ft^2*°R^4)

RADIATION_CONTROL_FACTOR = (0.9E-9) # how much radiative heat loss is scaled by... higher = more heat loss per tick

NATURAL_CONVECTION_COEFFICIENT = 0.5 # chatgpt says horizontal surfaces should be in 0.5-1 BTU/(ft^2 °F)

TEMPERATURE_SMOOTH_FACTOR = 0.003 # how much closer to average air temperature of their surroundings tiles get each smoothing iteration

# Material property dictionaries... maybe move to a per-material dictionary of propreties?
HEAT_CAPACITY = {
'stone':    0.23885,                    # BTU/lb F
'water':    1.001,                      # BTU/lb F
'ice':      0.5,                        # BTU/lb F
'air':      0.17128                     # BTU/lb F
}

DENSITY = {
'stone':    175,                        # lb / ft^3
'water':    62.4,                       # lb / ft^3
'ice':      57.24644,                   # lb / ft^3
'air':      0.075                       # lb / ft^3
}

ALBEDO = {
'stone':    0.35,
'water':    0.075,
'ice':      0.75,
'air':      0.3
}

CALC_DEPTH = {
'stone':    1,                         # ft 
'water':    300,                       # ft
'ice':      5,                         # ft
'air':      2500                          # ft
}

EMISSIVITY = {
'surface':  0.9,
'air':      0.7
}

# Graphics
TILE_GRAPHIC_SIZE = 64 # px

#####################
# CLASSES/FUNCTIONS #
#####################

class Tile:
    """Class which stores the data within one "tile", or
       a 1X1 mile square that has properties like surface
       temperature, elevation, and air temperature.
       Initializes to room temperature/sea level values."""

    def __init__(self, x, y):
        
        # Location
        self.x = x
        self.y = y
        
        # Surface values
        self.elevation = 0              # ft
        self.temperature = 70           # degrees F
        
        # Air values
        self.airTemperature = 70        # degrees F
        self.lastAirTemperature = 70    # degrees F
        self.airPressure = 14.7         # psi
        self.airDensity = 0.0765        # lb/ft^3
        
        # Calculation values
        self.airTempElevFactor = 1
        self.airPresElevFactor = 1
        self.airDensElevFactor = 1
        self.heatFromAir = 0
        
        # Wind values
        self.windSpeedMagnitude = 5     # mph
        self.windSpeedAngle = 0
        
        # Sun values
        self.sunIntensity = 0
        self.sunlightData = {}
        
        # Display values
        self.graphic = "blank"
        self.graphicOverlay = []
        self.type = None
        
        # Stores Tile objects of neighboring tiles
        self.neighbors = []

# Holds subclasses representing tile data as well as map dimensions, controls, etc.
class GameMap:
    """Stores all tile data."""

    #############################
    # UTILITY CLASSES/FUNCTIONS #
    #############################

    class XY_Data:
        """Utility class to store a pair of values 
           accesible by obj.x and obj.y."""
        def __init__(self, x, y):
            self.x = x
            self.y = y  


    class Map_Data:
        """Class used to store data for each tile,
           as a list of Tile objects."""
        def __init__(self, mapSize):
            # Generate map tile values
            self.tiles = []
            for i in range(mapSize):
                row = []
                for j in range(mapSize):
                    tile = Tile(i, j)
                    row.append(tile)
                self.tiles.append(row)
    
    
    ########################################
    # MAIN MAP CLASS FUNCTIONS AND CLASSES #
    ########################################

    def __init__(self, gameWindow, graphics, mapSize, antialiasing=True):
        
        # Initialize display values (not changing)
        self.tileCount = mapSize
        self.mapAreaTiles = self.tileCount ** 2
        self.gameWindow = gameWindow
        self.graphics = graphics
        self.antialiasing = antialiasing
        
        # Map display controls (changeable)
        self.displayMode = "Surface"
        self.windArrows = False
        self.displaySun = True

        # Sun settings
        self.sunGraphics = {}
        self.sunHourAngle = 0 # 0 to 360 degrees (0 is x=0)
        self.sunLatitude = 0 # 0 to 360 degrees (0 is half of map height)
        
        self.greenhouse = 0.0

        # Tie to contour class so it can extract min/max data
        self.contourEnabled = False
        self.contourMin = 0
        self.contourMax = 0
        self.contour = ContourBars(self.gameWindow)

        # Map controls (zoom/panning)
        self.zoomIncrement = int(0.1 * gameWindow.y)
        self.panLimitPaddingX = int(0.05 * gameWindow.y)
        self.panLimitPaddingY = int(0.05 * gameWindow.y)

        # Actual size = tile size in px * number of tiles
        mapSideLengthPixels = TILE_GRAPHIC_SIZE * self.tileCount
        self.mapLengthsPixels = self.XY_Data(mapSideLengthPixels, mapSideLengthPixels)
        self.mapAreaPixels = self.mapLengthsPixels.x * self.mapLengthsPixels.y

        # Initialize display size (modified on zoom)
        self.displaySize = self.XY_Data(self.mapLengthsPixels.x, self.mapLengthsPixels.y)

        # Initialize map in screen center
        self.origin = self.XY_Data(self.gameWindow.x/2 - self.displaySize.x/2, \
                                   self.gameWindow.y/2 - self.displaySize.y/2)

        # Generate map tile values (initially empty/blank, then algorithm run)
        self.seaLevel = 0
        self.mapData = self.Map_Data(self.tileCount)
        self.rand_gen()
        self.reset_tiles()
        self.calc_sun()
        self.reset_suntiles()

        # Collect neighboring tile objects for each tile
        self.collect_neighbors()

        # Print information to stdout
        log("Map Size: " + str(self.tileCount) + " x " + str(self.tileCount) + " tiles (" + str(self.mapLengthsPixels.x) + " x " + str(self.mapLengthsPixels.y) + " px)")
        log("Map Area: " + str(self.mapAreaTiles) + " tiles (" + str(self.mapAreaPixels) + " px)")

    
    def increase_greenhouse_effect(self, increment=GREENHOUSE_EFFECT_INCREMENT):
        """Increases greenhouse factor (or how much heat is retained by planet)."""
        self.greenhouse += increment
    
    
    def decrease_greenhouse_effect(self, increment=GREENHOUSE_EFFECT_INCREMENT):
        """Decreases greenhouse factor (or how much heat is retained by planet)."""
        self.greenhouse -= increment
    
    
    def collect_neighbors(self):      
        """Find all Tile objects that are surrounding each Tile object and
           store their references in a list as a property of that tile"""
        directions = [-1, 0, 1]
        neighborIndices = [(x, y) for x in directions for y in directions]
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                for neighborIndex in neighborIndices:
                    neighborX = i + neighborIndex[0]
                    if neighborX > self.tileCount-1: 
                        neighborX = 0
                    elif neighborX < 0:
                        neighborX = self.tileCount-1
                    neighborY = j + neighborIndex[1]   
                    if neighborY > self.tileCount-1: 
                        neighborY = 0
                    elif neighborY < 0:
                        neighborY = self.tileCount-1  
                    neighborTile = self.mapData.tiles[neighborX][neighborY]
                    tile.neighbors.append(neighborTile)
    
    
    def zoom(self, input):
        """Scales map surface to zoom."""
        zoomFactor = int(input * self.zoomIncrement)
        self.displaySize.x += zoomFactor
        self.displaySize.y += zoomFactor
        self.origin.x -= zoomFactor/2
        self.origin.y -= zoomFactor/2
        self.check_bounds()
        self.scale_map()
        if self.displaySun:
            self.scale_sun_map()

    
    def drag(self, relativePosition):
        """Apply changed mouse position (click and drag) to map."""
        self.origin.x += relativePosition[0]
        self.origin.y += relativePosition[1]
        self.check_bounds()


    def reset_view(self):
        """Reset display origin and size to recenter view."""
        self.displaySize.x = self.mapLengthsPixels.x
        self.displaySize.y = self.mapLengthsPixels.y
        self.origin.x = self.gameWindow.x/2 - self.displaySize.x/2
        self.origin.y = self.gameWindow.y/2 - self.displaySize.y/2
        self.check_bounds()


    def check_bounds(self):
        """A function that checks if map is not out of the bounds of the screen.
           Edges of displayed map are locked inside the edges of the screen.
           If zoomed too far in map is scaled up."""
    
        # Set to min size if zoomed too far in
        if self.displaySize.x < 100:
            self.displaySize.x = 100
        if self.displaySize.y < 100:
            self.displaySize.y = 100
            
        # Limit panning
        if self.displaySize.x > self.gameWindow.x - 2*self.panLimitPaddingX and self.displaySize.x < self.gameWindow.x:
            self.origin.x = self.gameWindow.x/2 - self.displaySize.x/2
        elif self.displaySize.x > self.gameWindow.x:
            if self.origin.x > 0 + self.panLimitPaddingX:
                self.origin.x = 0 + self.panLimitPaddingX
            if self.origin.x + self.displaySize.x < self.gameWindow.x - self.panLimitPaddingX:
                self.origin.x = self.gameWindow.x - self.panLimitPaddingX - self.displaySize.x
        elif self.displaySize.x < self.gameWindow.x:
            if self.origin.x < 0 + self.panLimitPaddingX:
                self.origin.x = 0 + self.panLimitPaddingX
            if self.origin.x + self.displaySize.x > self.gameWindow.x - self.panLimitPaddingX:
                self.origin.x = self.gameWindow.x - self.panLimitPaddingX - self.displaySize.x
        if self.displaySize.y > self.gameWindow.y - 2*self.panLimitPaddingY and self.displaySize.y < self.gameWindow.y:
            self.origin.y = self.gameWindow.y/2 - self.displaySize.y/2
        elif self.displaySize.y > self.gameWindow.y:
            if self.origin.y > 0 + self.panLimitPaddingY:
                self.origin.y = 0 + self.panLimitPaddingY
            if self.origin.y + self.displaySize.y < self.gameWindow.y - self.panLimitPaddingY:
                self.origin.y = self.gameWindow.y - self.panLimitPaddingY - self.displaySize.y
        elif self.displaySize.y < self.gameWindow.y:
            if self.origin.y < 0 + self.panLimitPaddingY:
                self.origin.y = 0 + self.panLimitPaddingY
            if self.origin.y + self.displaySize.y > self.gameWindow.y - self.panLimitPaddingY:
                self.origin.y = self.gameWindow.y - self.panLimitPaddingY - self.displaySize.y


    def rand_gen(self):
        """Random generation of world map."""
    
        seedCount = int(self.mapAreaTiles / 2)
        elevationBounds = (-40000, 60000)
        avgOceanDepth = -12500
        seedList = []
        smoothingIterations = 2
        totalIterations = 25
        elevationNoiseFreq = 5
        elevationNoiseMax = 100
        percentHighElev = 0.4
        
        maxTemperature = 75
        minTemperature = -15
        temperatureNoiseFreq = 2
        temperatureNoiseMax = 10
        airTemperatureNoiseFreq = 1
        airTemperatureNoiseMax = 10
        
        # Parabolic temperature equation - input is "latitude", a value between -1 and 1
        def temperature_curve(latitude):
            return maxTemperature + (-maxTemperature + minTemperature) * latitude**2

        # Set to baseline (water at average ocean depth)
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                tile.graphic = "water"
                tile.elevation = avgOceanDepth
        
        # Set random seed tiles to random elevations
        for t in range(totalIterations):
            for s in range(seedCount):
                randomX = random.randint(0, self.tileCount-1)
                randomY = random.randint(0, self.tileCount-1)
                if random.random() < percentHighElev:
                    randomZ = random.randint(0, elevationBounds[1])
                else:
                    randomZ = random.randint(elevationBounds[0], 0)
                seedList.append((randomX, randomY, randomZ))
                tile = self.mapData.tiles[randomX][randomY]
                tile.elevation = randomZ
                
            # Average elevations of tiles
            for h in range(smoothingIterations):
                for i in range(self.tileCount):
                    for j in range(self.tileCount):
                    
                        # Get current/focus tile data
                        tile = self.mapData.tiles[i][j]
                        adjTilesElev = []
                        
                        # Get nine neighboring tiles (including current)
                        for k in [-1, 0, 1]:
                            for l in [-1, 0, 1]:
                            
                                # Get neighboring tiles (loop around if at edge)
                                adjIndexX = i+k
                                if adjIndexX >= self.tileCount:
                                    adjIndexX = 0
                                elif adjIndexX < 0:
                                    adjIndexX = self.tileCount-1
                                adjIndexY = j+l
                                if adjIndexY >= self.tileCount:
                                    adjIndexY = 0
                                elif adjIndexY < 0:
                                    adjIndexY = self.tileCount-1
                                    
                                # Add elevation of neighboring tile to list
                                adjTile = self.mapData.tiles[adjIndexX][adjIndexY]
                                adjTilesElev.append(float(adjTile.elevation))
                                
                        avgElevation = sum(adjTilesElev) / 9
                        effectiveElevation = avgElevation
                        
                        # Add random noise to elevation
                        if random.randint(0, elevationNoiseFreq-1) == 0:
                            effectiveElevation += random.randint(-1*elevationNoiseMax, elevationNoiseMax)
                        tile.elevation = int(effectiveElevation)

        # Apply parabolic temperature curve (simulate equatorial effect)
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                latitudeValuePercent = (float(j) - self.tileCount/2.0) / (self.tileCount/2)
                temperature = temperature_curve(latitudeValuePercent)
                airTemperature = temperature_curve(latitudeValuePercent)
                
                # Add random noise to temperature
                if random.randint(0, temperatureNoiseFreq-1) == 0:
                    temperature += random.randint(-1*temperatureNoiseMax, temperatureNoiseMax)
                if tile.elevation > 0:
                    temperature += random.randint(0, 50)
                    
                # Add random noise to air temperature
                #if random.randint(0, airTemperatureNoiseFreq-1) == 0:
                #    airTemperature += random.randint(-1*airTemperatureNoiseMax, airTemperatureNoiseMax)
                    
                tile.temperature = temperature
                tile.airTemperature = float(airTemperature)
                
        # Calculate air pressure from temperature        
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                airTemperature = tile.airTemperature
                airTempRankine = airTemperature + 459.67
                idealGasConst = 10.731577089016  # psi * ft3 / lbmol * °R
                volumeOfTile = 5280.0**3.0 # 1 cubic mile to feet cubed
                molesOfTile = ((4.168 * 10.0**12.0) / 24.0) * 0.00220462 # lbmols in one cubic mile
                
                # Ideal gas law estimation
                tile.airPressure = (molesOfTile * idealGasConst * airTempRankine) / volumeOfTile
                
        self.elevation_calcs()
        
        # Run a few times to smooth out initial values
        #for i in range(3):
            #self.calc_velocity()
              
              

    def elevation_calcs(self):
        """A function run at startup to calculate impact of current elevation of
           tile on the effective temperature/pressure at the surface. 
           The physical effect is known as Lapse Rate.
           Data is saved as lists to each Tile object for quick lookup."""
    
        # Apply effect to temp, pressure, and density according to tile elevation
        # Values should represent air at whatever elevation is just above surface (incl. ocean surface)
        # Should only apply once !!! after initial value generation (rand_gen)
    
        # Source: https://www.engineeringtoolbox.com/standard-atmosphere-d_604.html
        # Conversion factors to adjust temp/pressure/density to elevation
        # Second-order curve fits to first three data points
        def temp_from_elev(elevation):
            return 1.0000 - (6 * 10**(-5) * elevation) + (5 * 10**(-12) * elevation**2)
        def pressure_from_elev(elevation):
            return 1.0004 - (4 * 10**(-5) * elevation) + (5 * 10**(-10) * elevation**2)
        def density_from_elev(elevation):
            return 1.0001 - (3 * 10**(-5) * elevation) + (3 * 10**(-10) * elevation**2)
        
        # Adjust temp/pressure/density from elevation        
        for i in range(self.tileCount):
            for j in range(self.tileCount):
            
                # Get tile elevation data
                tile = self.mapData.tiles[i][j]
                tileElevation = tile.elevation
                
                # Air "elevation" on oceans should be at sea level
                if tileElevation < self.seaLevel:
                    tileElevation = 0.0
                    
                    self.airTempElevFactor = temp_from_elev(tileElevation)
                    self.airPresElevFactor = pressure_from_elev(tileElevation)
                    self.airDensElevFactor = density_from_elev(tileElevation)   
                    
                # Apply equations to adjust unadjusted temps/pressures/densities to elevation
                # TODO: Should only air density be affected? Since T/P are tied to this, they should be affected on calc steps
                tile.airTemperature = tile.airTemperature * temp_from_elev(tileElevation)
                tile.temperature = tile.temperature * temp_from_elev(tileElevation)
                tile.airPressure = tile.airPressure * pressure_from_elev(tileElevation)
                tile.airDensity = tile.airDensity * density_from_elev(tileElevation)


    def smooth_temps(self):
        """Averages temperatures across each tile and its eight neighbors,
           applying only a percentage of the difference between the average
           and the actual to simulate slower diffusion."""
        directions = [-1, 0, 1]
        neighborIndices = [(x, y) for x in directions for y in directions]
        allTileIndices = [(x, y) for x in range(self.tileCount) for y in range(self.tileCount)]
        random.shuffle(allTileIndices)
        for tileIndex in allTileIndices:
            tile = self.mapData.tiles[tileIndex[0]][tileIndex[1]]
            airTemperature = tile.airTemperature
            totalTemperature = airTemperature
            for neighborTile in tile.neighbors:
                totalTemperature += neighborTile.airTemperature
            averageTemperature = totalTemperature / 9
            tile.airTemperature += (averageTemperature - tile.airTemperature) * TEMPERATURE_SMOOTH_FACTOR
            for neighborTile in tile.neighbors:
                neighborTile.airTemperature += (averageTemperature - neighborTile.airTemperature) * TEMPERATURE_SMOOTH_FACTOR


    def heat_calcs(self):
        """Calculate input and output heats to each tile (both surface and air) and
           calculate the resulting temperature change. Includes transfer of heat
           between air and surface. Includes radiative and convective effects.
           No conduction is used due to the large scale of each tile. All calculations
           currently rely on fact that each tick/iteration is a single hour.
           TODO: add in "time step size" as a factor for all calcs so it can be adjusted."""
        debug = False
    
        # DEBUGGING
        if debug:
            worldHeatGainSum = 0
            worldHeatLossSum = 0
            worldSurfaceHeatGainSum = 0
            worldSurfaceHeatLossSum = 0
            worldAirHeatGainSum = 0
            worldAirHeatLossSum = 0
    
        # Change temp of tiles in sunlight      
        for i in range(self.tileCount):
            for j in range(self.tileCount):
            
                # Get tile data
                tile = self.mapData.tiles[i][j]
                tileType = tile.type
                surfaceTemperature = tile.temperature
                airTemperature = tile.airTemperature
                airRadiationToSurface = tile.heatFromAir
                surfaceTemperatureRankine = surfaceTemperature + 459.67
                airTemperatureRankine = airTemperature + 459.67
                cosineSolarZenithAngle = tile.sunlightData[self.sunHourAngle]
                
                airTempElevFactor = self.airTempElevFactor
                
                # Correct for values below absolute zero
                if surfaceTemperatureRankine < 0:
                    tile.temperature = surfaceTemperature = -459.67
                    surfaceTemperatureRankine = 0
                if airTemperatureRankine < 0:
                    tile.airTemperature = airTemperature = -459.67
                    airTemperatureRankine = 0
                
                # Allow heat input if tile is in sunlight
                # Scale by latitude (lower at poles)
                sunHeatIn = BASE_SUN_HEAT_FLUX * cosineSolarZenithAngle


                # Snow/sea ice inherits ice material properties
                if tileType == 'snow' or tileType == 'sea_ice':
                    material = 'ice'
                else:
                    material = tileType
                    
                # Collect material properties
                surfaceAlbedo = ALBEDO[material]
                heatCapacity = HEAT_CAPACITY[material]
                heatCalcDepth = CALC_DEPTH[material]
                
                # "Calc Depth" is used to calculate finite temp change - simplifying each tile to single point
                # with a "mass" determined by the volume and density, volume calculated from 1 mile * 1 mile * calc depth
                surfaceMass = DENSITY[material] * heatCalcDepth * 5280.0**2

                # Warm air or surface reduces albedo
                if tileType == "snow" or tileType == "ice":
                    if airTemperature > 32:
                        surfaceAlbedo -= 0.1
                    if surfaceTemperature > 32:
                        surfaceAlbedo -= 0.15

                # Uses Calc Depth as well, only simulating the first layer of air above the surface
                # TODO: once air gas calcs ironed out, use air density instead of static value
                airMass = (CALC_DEPTH['air'] * 5280**2) * DENSITY['air']
                 
                # Air to surface convection
                # Convection coefficient maxes out at 120mph wind and 175 W/m^2 K
                airConvCoefBounds = (0.088, 30.840) # 0.5 to 175 W/m^2 K in BTU/ft^2 F
                if tile.windSpeedMagnitude > 176.0: # 120mph -- 176 ft/s
                    airConvectionCoefficient = 1.0
                else:
                    airConvectionCoefficient = tile.windSpeedMagnitude / 176.0
                airConvectionCoefficient = airConvCoefBounds[0] + \
                                          (airConvCoefBounds[1] - airConvCoefBounds[0]) * (tile.windSpeedMagnitude / 176.0)**0.5
                airConvectionCoefficient = max(airConvectionCoefficient, NATURAL_CONVECTION_COEFFICIENT)
                
                # Surface roughness increase on surface area estimation
                # Rougher surface = more surface area for convection
                if tileType == 'stone':
                    roughnessFactor = 1.2
                elif tileType == 'snow':
                    roughnessFactor = 1.5
                else:
                    roughnessFactor = 1
                
                # Calculate surface/air temperature difference
                deltaTemp = airTemperature - surfaceTemperature
                
                # BTU from (BTU/ft^2 F) * (ft^2) * (degrees F)
                convectionEnergy = (airConvectionCoefficient*roughnessFactor) * (5280**2) * deltaTemp
                
                # Add convective heat gain if positive
                if convectionEnergy > 0:
                    airConvectionToSurface = convectionEnergy
                else:
                    airConvectionToSurface = 0

                # Add convective heat loss if negative
                if convectionEnergy < 0:
                    surfaceConvectionToAir = -1*convectionEnergy
                else:
                    surfaceConvectionToAir = 0
                
                # Calculate energy breakdown for surface
                # apply greenhouse factor to percent of sun energy absorbed by atmosphere
                # remaining energy goes to surface
                percentSunHeatToAir = HEAT_RATIO_AIR
                percentSunHeatToSurface = 1 - percentSunHeatToAir
                
                ########################
                # Surface heat transfer
                ########################
                
                # IN: sun radiation, atmosphere re-radiation, hot air convection
                
                # Add energy from sun
                sunHeatToSurface = (percentSunHeatToSurface * sunHeatIn)
                sunHeatToSurfaceAbsorbed = sunHeatToSurface * (1 - surfaceAlbedo)

                # OUT: radiation to air, reflected sun radiation, cold air convection
                # TODO: when water system active, heat lost through latent heat, or evaporative heat loss

                # Radiation back to air
                surfaceRadiation = RADIATION_CONTROL_FACTOR * STEFAN_BOLTZMANN_CONSTANT * EMISSIVITY['surface'] * (5280.0**2) * surfaceTemperatureRankine**4.0
                
                # Reflected sun radiation
                surfaceReflection = sunHeatToSurface * surfaceAlbedo

                ### SUM GAINS
                totalSurfaceHeatGain = sunHeatToSurfaceAbsorbed + airRadiationToSurface + airConvectionToSurface
                
                ### SUM LOSSES
                totalSurfaceHeatLoss = surfaceRadiation + surfaceConvectionToAir
                
                ### NET HEAT CHANGE
                surfaceNetHeat = totalSurfaceHeatGain - totalSurfaceHeatLoss
                surfaceDeltaTemperature = surfaceNetHeat / (surfaceMass * heatCapacity)
                tile.temperature = surfaceTemperature + surfaceDeltaTemperature

                ####################
                # Air heat transfer
                ####################
                
                # IN: sun radiation, surface re-radiation, hot surface convection, a percent of surface reflected energy

                # Add energy from sun
                sunHeatToAir = (percentSunHeatToAir * sunHeatIn)
                sunHeatToAirAbsorbed = sunHeatToAir * (1 - ALBEDO['air'])

                # Reabsorb surface radiation
                surfaceRadiationToAir = surfaceRadiation * (SURFACE_RADIATION_ABSORPTION_AIR * (1 + self.greenhouse))
                
                # Reabsorb surface reflection
                surfaceReflectionToAir = surfaceReflection * (REFLECTION_RATIO_SURFACE_TO_AIR * (1 + self.greenhouse))
                
                # OUT: radiation to surface/space, reflected sun radiation, cold surface convection
                
                # Radiation to space and surface (50/50)
                airRadiation = RADIATION_CONTROL_FACTOR * STEFAN_BOLTZMANN_CONSTANT * (EMISSIVITY['air'] * (1 + self.greenhouse)) * (5280.0**2) * airTemperatureRankine**4.0
                
                # Atmosphere reflection of sun radiation
                airReflectionToSpace = sunHeatToAir * ALBEDO['air']

                ### SUM GAINS
                totalAirHeatGain = sunHeatToAirAbsorbed + surfaceRadiationToAir + surfaceConvectionToAir + surfaceReflectionToAir
                
                ### SUM LOSSES
                totalAirHeatLoss = airRadiation + airConvectionToSurface
                
                ### NET HEAT CHANGE
                airNetHeat = totalAirHeatGain - totalAirHeatLoss
                airDeltaTemperature = airNetHeat / (airMass * HEAT_CAPACITY['air'])

                # By default, half of radiation from atmosphere reabsorbed by the surface
                tile.heatFromAir = airRadiation * RADIATION_RATIO_AIR_TO_SURFACE

                if airDeltaTemperature < 0:
                    airTempElevFactor = 1

                # Save previous value to calculate change in pressure/density
                tile.lastAirTemperature = float(airTemperature)
                tile.airTemperature = airTemperature + airDeltaTemperature * airTempElevFactor 
                
                if debug:
                
                    worldHeatGainSum += (totalAirHeatGain + totalSurfaceHeatGain) / 1E20
                    worldHeatLossSum += (totalAirHeatLoss + totalSurfaceHeatLoss) / 1E20 
                    worldSurfaceHeatGainSum += (totalSurfaceHeatGain) / 1E20
                    worldSurfaceHeatLossSum += (totalSurfaceHeatLoss) / 1E20
                    worldAirHeatGainSum += (totalAirHeatGain) / 1E20
                    worldAirHeatLossSum += (totalAirHeatLoss) / 1E20
                    
                    print('---')
                    print('Net heat surface: ' + str(surfaceNetHeat))
                    print('Total heat gain surface: ' + str(totalSurfaceHeatGain))
                    print('Total heat loss surface: ' + str(totalSurfaceHeatLoss))
                    print('Sun heating surface: ' + str(sunHeatToSurfaceAbsorbed))
                    print('Air radiation heating surface: ' + str(airRadiationToSurface))
                    print('Convection heating surface: ' + str(airConvectionToSurface))
                    print('Radiation heat loss surface: ' + str(surfaceRadiation))
                    print('Convection heat loss surface: ' + str(surfaceConvectionToAir))
                    print('Surface temp: ' + str(surfaceTemperature))
                    print('Air temp: ' + str(airTemperature))
                    print('Tile lit: ' + str(tileLit))
                    print('Radiation heat loss air: ' + str(airRadiation))

        if debug:
            print('---')
            print("Total world heat gain = " + str(worldHeatGainSum) + " E20 BTU")
            print("Total world heat loss = " + str(worldHeatLossSum) + " E20 BTU")
            print("Total world surface heat gain = " + str(worldSurfaceHeatGainSum) + " E20 BTU")
            print("Total world surface heat loss = " + str(worldSurfaceHeatLossSum) + " E20 BTU") 
            print("Total world air heat gain = " + str(worldAirHeatGainSum) + " E20 BTU")
            print("Total world air heat loss = " + str(worldAirHeatLossSum) + " E20 BTU")


    def calc_velocity(self):
        """Use Bernoulli's equation and air pressures to modify wind vectors."""
        
        # Shuffle tiles as to avoid order of operations influencing result
        tileListX = list(range(self.tileCount))
        tileListY = list(range(self.tileCount))
        random.shuffle(tileListX)
        random.shuffle(tileListY)
        
        # Loop through randomized tile lists
        for i in tileListX:
            for j in tileListY:
                
                # Get current tile data
                tile = self.mapData.tiles[i][j]
                tileAirPressure = tile.airPressure
                tileAirVelocityMagnitude = tile.windSpeedMagnitude
                tileAirVelocityAngle = tile.windSpeedAngle
                tileAirDensity = tile.airDensity
                                            
                # Initialize x/y components so adjacent tiles' effects can be added                            
                velocityComponentSumX = tileAirVelocityMagnitude * math.sin(math.radians(tileAirVelocityAngle))
                velocityComponentSumY = tileAirVelocityMagnitude * math.cos(math.radians(tileAirVelocityAngle))

                # Get eight neighboring tiles (excluding current)
                tileForceVectors = []
                tileVelocityVectors = []
                for k in [-1, 0, 1]:
                    for l in [-1, 0, 1]:
                        if not (k == 0 and l == 0):
                        
                            # Get neighboring tiles (loop around if at edge)
                            adjIndexX = i+k
                            if adjIndexX >= self.tileCount:
                                adjIndexX = 0
                            elif adjIndexX < 0:
                                adjIndexX = self.tileCount-1
                            adjIndexY = j+l
                            if adjIndexY >= self.tileCount:
                                adjIndexY = 0
                            elif adjIndexY < 0:
                                adjIndexY = self.tileCount-1

                            # Figure out angle to adjacent tile (0 degrees is up)
                            if k == -1 and l == -1:
                                adjAngle = 315
                            elif k == -1 and l == 0:
                                adjAngle = 270
                            elif k == -1 and l == 1:
                                adjAngle = 225
                            elif k == 0 and l == 1:
                                adjAngle = 180
                            elif k == 1 and l == 1:
                                adjAngle = 135
                            elif k == 1 and l == 0:
                                adjAngle = 90
                            elif k == 1 and l == -1:
                                adjAngle = 45
                            elif k == 0 and l == -1:
                                adjAngle = 0

                            adjTile = self.mapData.tiles[adjIndexX][adjIndexY]
                            adjTileAirPressure = adjTile.airPressure
                            adjTileAirVelocityMagnitude = adjTile.windSpeedMagnitude
                            adjTileAirVelocityAngle = adjTile.windSpeedAngle
                            tileForceVectors.append((adjAngle, adjTileAirPressure))
                            tileVelocityVectors.append((adjAngle, tileAirVelocityMagnitude, adjTileAirVelocityAngle))

                for forceVector, velocityVector in zip(tileForceVectors, tileVelocityVectors):
                
                    adjPressureDirection = forceVector[0]
                    adjPressureMagnitude = forceVector[1]
                    
                    adjVelocityDirection = velocityVector[0]
                    adjVelocityMagnitude = velocityVector[1]
                    adjVelocityAngle = velocityVector[2]
                
                    outwardVelocityMagnitude = adjVelocityMagnitude * math.cos(math.radians(adjVelocityDirection + adjVelocityAngle))
                
                    # Bernoulli's equation
                    velocityMagnitude = math.sqrt(abs(outwardVelocityMagnitude**2 - ((tileAirPressure - adjPressureMagnitude)/(0.5*tileAirDensity))))
                    
                    # Add components to sum
                    velocityComponentSumX += velocityMagnitude * math.sin(math.radians(adjPressureDirection))
                    velocityComponentSumY += velocityMagnitude * math.cos(math.radians(adjPressureDirection))

                newAngleRadians = math.atan(velocityComponentSumX / velocityComponentSumY)
                tile.windSpeedAngle = math.degrees(newAngleRadians)
                tile.windSpeedMagnitude = math.sqrt(velocityComponentSumX**2 + velocityComponentSumY**2)


    def gas_calcs(self):
        """Use Ideal Gas Law and air temperature/density
           to solve for new air pressure."""
    
        # Loop through tiles
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                
                #######
                
                # Method - calculate delta pressure and apply
                
                # Get current tile data
                # tile = self.mapData.tiles[i][j]
                
                # Tile data to modify/calculate values
                # tileAirDensity = tile.airDensity # lb/ft^3
                # tileAirTemperature = tile.airTemperature # fahrenheit
                # tileLastAirTemperature = tile.lastAirTemperature # fahrenheit
                # tileAirPressure = tile.airPressure # psi

                # gasConstant = 53.353 # ft lbf / lb R
                # psfToPsi = 0.00694444 # sq ft to sq in
                
                # deltaTemperature = tileAirTemperature - tileLastAirTemperature
                
                # Ideal gas law 
                # Delta P = density * gas const * delta T
                # pressureIncr = tileAirDensity * gasConstant * deltaTemperature * psfToPsi
                # tileAirPressureNew = tileAirPressure + pressureIncr
                # tile.airPressure = tileAirPressureNew
                
                #######
                
                # Method - calculate pressure directly from P = density * R * T
                
                # Get current tile data
                tile = self.mapData.tiles[i][j]
                
                # Tile data to modify/calculate values
                tileAirDensity = tile.airDensity # lb/ft^3
                tileAirTemperature = tile.airTemperature # fahrenheit
                tileAirTemperatureRankine = tileAirTemperature + 459.67
                tileAirPressure = tile.airPressure # psi

                gasConstant = 53.353 # ft lbf / lb R
                psfToPsi = 0.00694444 # sq ft to sq in

                # Ideal gas law 
                # P = density * gas const * T
                tile.airPressure = tileAirDensity * gasConstant * tileAirTemperatureRankine * psfToPsi


    def calc_temp_and_pressure(self):
        """Calculates wind speed and velocity from temp/pressure."""
    
        # Shuffle tiles as to avoid order of operations influencing result
        tileListX = list(range(self.tileCount))
        tileListY = list(range(self.tileCount))
        random.shuffle(tileListX)
        random.shuffle(tileListY)
        
        # Loop through randomized tile lists
        for i in tileListX:
            for j in tileListY:
                
                # Get current tile data
                tile = self.mapData.tiles[i][j]
                tileAirVelocityMagnitude = tile.windSpeedMagnitude
                tileAirVelocityAngle = tile.windSpeedAngle
                
                # Tile data to modify
                tileAirDensity = tile.airDensity # maybe not density - see note in elev calcs
                tileAirTemperature = tile.airTemperature
                tileAirPressure = tile.airPressure
                                            
                # Initialize x/y components so adjacent tiles' effects can be added                            
                velocityComponentSumX = tileAirVelocityMagnitude * math.sin(math.radians(tileAirVelocityAngle))
                velocityComponentSumY = tileAirVelocityMagnitude * math.cos(math.radians(tileAirVelocityAngle))

                # Get eight neighboring tiles (excluding current)
                adjTileData = []
                for k in [-1, 0, 1]:
                    for l in [-1, 0, 1]:
                        if not (k == 0 and l == 0):
                        
                            # Get neighboring tiles (loop around if at edge)
                            adjIndexX = i+k
                            if adjIndexX >= self.tileCount:
                                adjIndexX = 0
                            elif adjIndexX < 0:
                                adjIndexX = self.tileCount-1
                            adjIndexY = j+l
                            if adjIndexY >= self.tileCount:
                                adjIndexY = 0
                            elif adjIndexY < 0:
                                adjIndexY = self.tileCount-1

                            # Figure out angle to adjacent tile (0 degrees is up)
                            if k == -1 and l == -1:
                                adjAngle = 315
                            elif k == -1 and l == 0:
                                adjAngle = 270
                            elif k == -1 and l == 1:
                                adjAngle = 225
                            elif k == 0 and l == 1:
                                adjAngle = 180
                            elif k == 1 and l == 1:
                                adjAngle = 135
                            elif k == 1 and l == 0:
                                adjAngle = 90
                            elif k == 1 and l == -1:
                                adjAngle = 45
                            elif k == 0 and l == -1:
                                adjAngle = 0
                                
                            # Only tiles within 90 degrees of wind direction will exchange temp/pressure
                            tileAngleFactor = abs(tileAirVelocityAngle - adjAngle)    
                            if tileAngleFactor < 90:
                                adjTile = self.mapData.tiles[adjIndexX][adjIndexY]
                                adjTileAirPressure = adjTile.airPressure
                                adjTileAirTemperature = adjTile.airTemperature
                                adjTileAirDensity = adjTile.airDensity
                                adjTileData.append((adjAngle, adjTile))

                for adjTileItem in adjTileData:
                
                    adjPressureDirection = forceVector[0]
                    adjPressureMagnitude = forceVector[1]
        
                    adjVelocityDirection = velocityVector[0]
                    adjVelocityMagnitude = velocityVector[1]
                    adjVelocityAngle = velocityVector[2]
                
                newAngleRadians = math.atan(velocityComponentSumX / velocityComponentSumY)
                tile.windSpeedAngle = math.degrees(newAngleRadians)
                tile.windSpeedMagnitude = math.sqrt(velocityComponentSumX**2 + velocityComponentSumY**2)


    def update_map(self):
        """Update map surface with any new changes.
           Currently, this function just refreshes
           all tiles every call.
           TODO: set an ".updated" variable switch
           that can be caught by this function so
           only those tiles need to be changed."""
    
        # Create a surface and pass in a tuple containing its length and width
        self.mapSurface = pygame.Surface((self.mapLengthsPixels.x, self.mapLengthsPixels.y))
        self.mapSurface.fill((120, 120, 120))
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                tileType = tile.graphic
                currentPosition = (i*TILE_GRAPHIC_SIZE, j*TILE_GRAPHIC_SIZE)
                tileGraphic = self.graphics.data[tileType]
                self.mapSurface.blit(tileGraphic, currentPosition)
                if self.windArrows:
                    arrowImage = self.graphics.data["arrow"]
                    rotate_center(self.mapSurface, arrowImage, currentPosition, tile.windSpeedAngle)
                if tile.graphicOverlay != []:
                    for overlay in tile.graphicOverlay:
                        graphicOverlayType = overlay[0]
                        graphicOverlay = self.graphics.data[graphicOverlayType]
                        tileOverlayAngle = overlay[1]
                        rotate_center(self.mapSurface, graphicOverlay, currentPosition, tileOverlayAngle)


    def reset_suntiles(self):
        """Pulls pre-loaded sun surface (includes "darkness"
           and sun icon for a specific time of day) and scale
           to current display settings."""
    
        # Generate blank map layer
        self.sunLayerSurface = self.sunGraphics[self.sunHourAngle]
        self.scale_sun_map()


    def calc_sun(self):
        """A function run at startup to calculate position of sun and whether each
           tile is sun-lit at each time increment in the simulation (0-24hr).
           Data is saved as lists to each Tile object for quick lookup."""

        # Load sun graphics
        sunGraphic = self.graphics.data["sun"]
        shadowImage = self.graphics.data["shadow_50percent"]

        # Determine the angular change of the sun for each time step
        # 1 hr = 15 deg, 0.5 hr = 7.5 deg, etc.
        sunDataResolution = int(360 / (24 / TIME_STEP))
        
        # Loop through degrees of Hour Angle (only the correct Hour Angle at center of sun location)
        for hourAngleCenter in range(0, 360, sunDataResolution):

            # Generate blank map layer
            sunLayerSurface = pygame.Surface((self.mapLengthsPixels.x, self.mapLengthsPixels.y), pygame.SRCALPHA)
            sunLayerSurface.fill((255, 255, 255, 0))

            # Calculate center location of sun on map
            dieoutFactor = 1.475
            
            # Determine position of the sun based on hour angle/latitude
            halfTileCount = float(self.tileCount) / 2.0
            sunPositionY = halfTileCount + (self.sunLatitude / 90) * halfTileCount
            sunPositionX = float(self.tileCount) * (hourAngleCenter / 360.0)
            sunPosition = (sunPositionX * TILE_GRAPHIC_SIZE, sunPositionY * TILE_GRAPHIC_SIZE)
            sunLayerSurface.blit(sunGraphic, sunPosition)

            # Latitude factors calculated based on Mercator Projection (1/cos(lat))
            latitudeFactorBase = 1.0 / math.cos(math.radians(self.sunLatitude / dieoutFactor))

            # Calculate base dimensions of sunlit area on map
            sunlightWidthBase = float(self.tileCount) / 4.0
            sunlightWidth = sunlightWidthBase * latitudeFactorBase
            sunlightHeight = float(self.tileCount) / 2.0
            
            # Calculate Solar Zenith Angles, effective solar radiation coefficients,
            # and save sun graphics for each time step/tick
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    
                    latitudeAngle = abs(90 - ((180/(self.tileCount-1))*j))
                    latitudeAngleRadians = math.radians(latitudeAngle)
                    
                    solarDeclinationAngle = 0
                    solarDeclinationAngleRadians = math.radians(solarDeclinationAngle)
                    
                    # Calculate correct hour angle of each tile (with respect to current
                    deltaPositionX = (i - sunPositionX + self.tileCount) % self.tileCount
                    if deltaPositionX > halfTileCount:
                        deltaPositionX = deltaPositionX - self.tileCount
                    
                    hourAngleEffective = (360 / self.tileCount) * deltaPositionX
                    hourAngleRadians = math.radians(hourAngleEffective)
                    
                    # Solar Zenith Angle -- cos(Z) = sin(phi) * sin(delta) + cos(phi) * cos(delta) * cos(h)
                    cosineSolarZenithAngle = math.sin(latitudeAngleRadians) * math.sin(solarDeclinationAngleRadians) + \
                                             math.cos(latitudeAngleRadians) * math.cos(solarDeclinationAngleRadians) * math.cos(hourAngleRadians)

                    shadowGraphicAlpha = 255*(1-cosineSolarZenithAngle)
                    if shadowGraphicAlpha > 255:
                        shadowGraphicAlpha = 255
                    elif shadowGraphicAlpha < 0:
                        shadowGraphicAlpha = 0
                        
                    shadowImage.set_alpha(shadowGraphicAlpha)
                    currentPosition = (i * TILE_GRAPHIC_SIZE, j * TILE_GRAPHIC_SIZE)
                    sunLayerSurface.blit(shadowImage, currentPosition)
                    self.mapData.tiles[i][j].sunlightData.update({hourAngleCenter: cosineSolarZenithAngle})

            self.sunGraphics.update({hourAngleCenter: sunLayerSurface})


    def reset_tiles(self):
        """Takes current tile settings (dependent on
           tile properties, e.g. ice on tiles below
           freezing), fetches pre-loaded graphic and 
           adds to correct location on map surface."""
    
        # Default tile graphics display
        if self.displayMode == "Surface":
            self.contourEnabled = False
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    tile.graphicOverlay = []
                    tile.graphicOverlayAngle = []
                    if tile.elevation >= self.seaLevel:
                        if tile.temperature < 32:
                            tile.graphic = "snow"
                            tile.type = "snow"
                        else:
                            tile.type = "stone"
                            if tile.elevation > 9000:
                                tile.graphic = "stone9"
                            elif tile.elevation > 8000:
                                tile.graphic = "stone8"
                            elif tile.elevation > 7000:
                                tile.graphic = "stone7"
                            elif tile.elevation > 6000:
                                tile.graphic = "stone6"
                            elif tile.elevation > 5000:
                                tile.graphic = "stone5"
                            elif tile.elevation > 4000:
                                tile.graphic = "stone4"
                            elif tile.elevation > 3000:
                                tile.graphic = "stone3"
                            elif tile.elevation > 2000:
                                tile.graphic = "stone2"
                            elif tile.elevation > 1000:
                                tile.graphic = "stone1"
                            else:
                                tile.graphic = "stone0"
                    elif tile.elevation < self.seaLevel:
                        if tile.temperature > 28:
                            tile.graphic = "water"
                            tile.type = "water"
                        else:
                            tile.graphic = "sea_ice"
                            tile.type = "sea_ice"

        # Contour-band elevation display
        elif self.displayMode == "Elevation":
            self.contourEnabled = True
            tileElevationMax = 15000
            tileElevationMin = -9000
            self.contourMin = tileElevationMin
            self.contourMax = tileElevationMax
            tileElevationDifference = tileElevationMax - tileElevationMin
            tileElevationIncr = tileElevationDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    if tile.elevation >= tileElevationMax:
                        tile.graphic = "band0"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*0 and tile.elevation >= tileElevationMax - tileElevationIncr*1:
                        tile.graphic = "band1"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*1 and tile.elevation >= tileElevationMax - tileElevationIncr*2:
                        tile.graphic = "band2"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*2 and tile.elevation >= tileElevationMax - tileElevationIncr*3:
                        tile.graphic = "band3"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*3 and tile.elevation >= tileElevationMax - tileElevationIncr*4:
                        tile.graphic = "band4"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*4 and tile.elevation >= tileElevationMax - tileElevationIncr*5:
                        tile.graphic = "band5"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*5 and tile.elevation >= tileElevationMax - tileElevationIncr*6:
                        tile.graphic = "band6"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*6 and tile.elevation >= tileElevationMax - tileElevationIncr*7:
                        tile.graphic = "band7"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*7 and tile.elevation >= tileElevationMax - tileElevationIncr*8:
                        tile.graphic = "band8"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*8 and tile.elevation >= tileElevationMax - tileElevationIncr*9:
                        tile.graphic = "band9"
                    elif tile.elevation <= tileElevationMax - tileElevationIncr*9:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"                                     
                        
        elif self.displayMode == "Elevation, Land-Only":
            self.contourEnabled = True
            tileElevationMax = 15000
            tileElevationMin = self.seaLevel
            self.contourMin = tileElevationMin
            self.contourMax = tileElevationMax
            tileElevationDifference = tileElevationMax - tileElevationMin
            tileElevationIncr = tileElevationDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    if tile.elevation >= tileElevationMax:
                        tile.graphic = "band0"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*0 and tile.elevation >= tileElevationMax - tileElevationIncr*1:
                        tile.graphic = "band1"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*1 and tile.elevation >= tileElevationMax - tileElevationIncr*2:
                        tile.graphic = "band2"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*2 and tile.elevation >= tileElevationMax - tileElevationIncr*3:
                        tile.graphic = "band3"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*3 and tile.elevation >= tileElevationMax - tileElevationIncr*4:
                        tile.graphic = "band4"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*4 and tile.elevation >= tileElevationMax - tileElevationIncr*5:
                        tile.graphic = "band5"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*5 and tile.elevation >= tileElevationMax - tileElevationIncr*6:
                        tile.graphic = "band6"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*6 and tile.elevation >= tileElevationMax - tileElevationIncr*7:
                        tile.graphic = "band7"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*7 and tile.elevation >= tileElevationMax - tileElevationIncr*8:
                        tile.graphic = "band8"
                    elif tile.elevation < tileElevationMax - tileElevationIncr*8 and tile.elevation >= tileElevationMax - tileElevationIncr*9:
                        tile.graphic = "band9"
                    elif tile.elevation <= tileElevationMin:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"                    
                        
        elif self.displayMode == "Surface Temperature":
            self.contourEnabled = True
            tileTemperatureMax = 120
            tileTemperatureMin = -50
            self.contourMin = tileTemperatureMin
            self.contourMax = tileTemperatureMax
            tileTemperatureDifference = tileTemperatureMax - tileTemperatureMin
            tileTemperatureIncr = tileTemperatureDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    if tile.temperature >= tileTemperatureMax:
                        tile.graphic = "band0"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*0 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*1:
                        tile.graphic = "band1"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*1 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*2:
                        tile.graphic = "band2"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*2 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*3:
                        tile.graphic = "band3"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*3 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*4:
                        tile.graphic = "band4"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*4 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*5:
                        tile.graphic = "band5"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*5 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*6:
                        tile.graphic = "band6"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*6 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*7:
                        tile.graphic = "band7"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*7 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*8:
                        tile.graphic = "band8"
                    elif tile.temperature < tileTemperatureMax - tileTemperatureIncr*8 and tile.temperature >= tileTemperatureMax - tileTemperatureIncr*9:
                        tile.graphic = "band9"
                    elif tile.temperature <= tileTemperatureMin:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"
                        
        elif self.displayMode == "Air Temperature":
            self.contourEnabled = True
            airTemperatureMax = 120
            airTemperatureMin = -50
            self.contourMin = airTemperatureMin
            self.contourMax = airTemperatureMax
            airTemperatureDifference = airTemperatureMax - airTemperatureMin
            airTemperatureIncr = airTemperatureDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    if tile.airTemperature >= airTemperatureMax:
                        tile.graphic = "band0"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*0 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*1:
                        tile.graphic = "band1"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*1 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*2:
                        tile.graphic = "band2"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*2 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*3:
                        tile.graphic = "band3"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*3 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*4:
                        tile.graphic = "band4"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*4 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*5:
                        tile.graphic = "band5"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*5 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*6:
                        tile.graphic = "band6"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*6 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*7:
                        tile.graphic = "band7"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*7 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*8:
                        tile.graphic = "band8"
                    elif tile.airTemperature < airTemperatureMax - airTemperatureIncr*8 and tile.airTemperature >= airTemperatureMax - airTemperatureIncr*9:
                        tile.graphic = "band9"
                    elif tile.airTemperature <= airTemperatureMin:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"
                        
        elif self.displayMode == "Air Pressure":
            self.contourEnabled = True
            airPressureMax = 15
            airPressureMin = 5
            self.contourMin = airPressureMin
            self.contourMax = airPressureMax
            airPressureDifference = airPressureMax - airPressureMin
            airPressureIncr = airPressureDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    if tile.airPressure >= airPressureMax:
                        tile.graphic = "band0"
                    elif tile.airPressure < airPressureMax - airPressureIncr*0 and tile.airPressure >= airPressureMax - airPressureIncr*1:
                        tile.graphic = "band1"
                    elif tile.airPressure < airPressureMax - airPressureIncr*1 and tile.airPressure >= airPressureMax - airPressureIncr*2:
                        tile.graphic = "band2"
                    elif tile.airPressure < airPressureMax - airPressureIncr*2 and tile.airPressure >= airPressureMax - airPressureIncr*3:
                        tile.graphic = "band3"
                    elif tile.airPressure < airPressureMax - airPressureIncr*3 and tile.airPressure >= airPressureMax - airPressureIncr*4:
                        tile.graphic = "band4"
                    elif tile.airPressure < airPressureMax - airPressureIncr*4 and tile.airPressure >= airPressureMax - airPressureIncr*5:
                        tile.graphic = "band5"
                    elif tile.airPressure < airPressureMax - airPressureIncr*5 and tile.airPressure >= airPressureMax - airPressureIncr*6:
                        tile.graphic = "band6"
                    elif tile.airPressure < airPressureMax - airPressureIncr*6 and tile.airPressure >= airPressureMax - airPressureIncr*7:
                        tile.graphic = "band7"
                    elif tile.airPressure < airPressureMax - airPressureIncr*7 and tile.airPressure >= airPressureMax - airPressureIncr*8:
                        tile.graphic = "band8"
                    elif tile.airPressure < airPressureMax - airPressureIncr*8 and tile.airPressure >= airPressureMax - airPressureIncr*9:
                        tile.graphic = "band9"
                    elif tile.airPressure <= airPressureMin:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"
    
        elif self.displayMode == "Air Density":
            self.contourEnabled = True
            airDensityMax = 0.08
            airDensityMin = 0.04
            self.contourMin = airDensityMin
            self.contourMax = airDensityMax
            airDensityDifference = airDensityMax - airDensityMin
            airDensityIncr = airDensityDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    if tile.airDensity >= airDensityMax:
                        tile.graphic = "band0"
                    elif tile.airDensity < airDensityMax - airDensityIncr*0 and tile.airDensity >= airDensityMax - airDensityIncr*1:
                        tile.graphic = "band1"
                    elif tile.airDensity < airDensityMax - airDensityIncr*1 and tile.airDensity >= airDensityMax - airDensityIncr*2:
                        tile.graphic = "band2"
                    elif tile.airDensity < airDensityMax - airDensityIncr*2 and tile.airDensity >= airDensityMax - airDensityIncr*3:
                        tile.graphic = "band3"
                    elif tile.airDensity < airDensityMax - airDensityIncr*3 and tile.airDensity >= airDensityMax - airDensityIncr*4:
                        tile.graphic = "band4"
                    elif tile.airDensity < airDensityMax - airDensityIncr*4 and tile.airDensity >= airDensityMax - airDensityIncr*5:
                        tile.graphic = "band5"
                    elif tile.airDensity < airDensityMax - airDensityIncr*5 and tile.airDensity >= airDensityMax - airDensityIncr*6:
                        tile.graphic = "band6"
                    elif tile.airDensity < airDensityMax - airDensityIncr*6 and tile.airDensity >= airDensityMax - airDensityIncr*7:
                        tile.graphic = "band7"
                    elif tile.airDensity < airDensityMax - airDensityIncr*7 and tile.airDensity >= airDensityMax - airDensityIncr*8:
                        tile.graphic = "band8"
                    elif tile.airDensity < airDensityMax - airDensityIncr*8 and tile.airDensity >= airDensityMax - airDensityIncr*9:
                        tile.graphic = "band9"
                    elif tile.airDensity <= airDensityMin:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"
    
        elif self.displayMode == "Wind Speed":
            ftPerSecToMPH = 0.681818
            self.contourEnabled = True
            windSpeedMax = 176
            windSpeedMin = 0
            self.contourMin = windSpeedMin * ftPerSecToMPH
            self.contourMax = windSpeedMax * ftPerSecToMPH
            windSpeedDifference = windSpeedMax - windSpeedMin
            windSpeedIncr = windSpeedDifference / 9.0 # for 11-band contour
            for i in range(self.tileCount):
                for j in range(self.tileCount):
                    tile = self.mapData.tiles[i][j]
                    tileX = i * TILE_GRAPHIC_SIZE
                    tileY = j * TILE_GRAPHIC_SIZE
                    if tile.windSpeedMagnitude >= windSpeedMax:
                        tile.graphic = "band0"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*0 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*1:
                        tile.graphic = "band1"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*1 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*2:
                        tile.graphic = "band2"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*2 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*3:
                        tile.graphic = "band3"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*3 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*4:
                        tile.graphic = "band4"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*4 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*5:
                        tile.graphic = "band5"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*5 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*6:
                        tile.graphic = "band6"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*6 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*7:
                        tile.graphic = "band7"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*7 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*8:
                        tile.graphic = "band8"
                    elif tile.windSpeedMagnitude < windSpeedMax - windSpeedIncr*8 and tile.windSpeedMagnitude >= windSpeedMax - windSpeedIncr*9:
                        tile.graphic = "band9"
                    elif tile.windSpeedMagnitude <= windSpeedMin:
                        tile.graphic = "band10"     
                    else:
                        tile.graphic = "blank"
    
    
        self.update_map()
        self.scale_map()


    def scale_map(self):
        """Scale map surface to current display settings."""
        if self.antialiasing is True:
            self.mapSurfaceScaled = pygame.transform.smoothscale(self.mapSurface, (self.displaySize.x, self.displaySize.y))
        else:
            self.mapSurfaceScaled = pygame.transform.scale(self.mapSurface, (self.displaySize.x, self.displaySize.y))


    def scale_sun_map(self):
        """Scale sun overlay surface to current display settings."""
        if self.antialiasing is True:
            self.sunLayerSurfaceScaled = pygame.transform.smoothscale(self.sunLayerSurface, (self.displaySize.x, self.displaySize.y))
        else:
            self.sunLayerSurfaceScaled = pygame.transform.scale(self.sunLayerSurface, (self.displaySize.x, self.displaySize.y))


    def get_map(self):
        """Quick function to return map surface."""
        return self.mapSurfaceScaled, (self.origin.x, self.origin.y)


    def get_sun_map(self):
        """Quick function to return sun overlay surface."""
        return self.sunLayerSurfaceScaled, (self.origin.x, self.origin.y)
