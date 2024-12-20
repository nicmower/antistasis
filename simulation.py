import math
import random
from graphics import *
from ui import *

# Map properties classes
class Map_Actual_Size:
    def __init__(self, sizePx):
        self.x = sizePx
        self.y = sizePx  
class Map_Display_Size:
    def __init__(self, sizeX, sizeY):
        self.x = sizeX
        self.y = sizeY
class Map_Origin:
    def __init__(self, originX, originY):
        self.x = originX
        self.y = originY


# Classes to hold map data
class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.elevation = 0 # feet
        self.temperature = 70 # fahrenheit
        
        self.airTemperature = 70 # fahrenheit
        self.lastAirTemperature = 70
        self.airPressure = 0 # psi (lb/in^2)
        self.airDensity = 0.076474252 # lb/ft^3
        
        self.airTempElevFactor = 1
        self.airPresElevFactor = 1
        self.airDensElevFactor = 1
        self.heatFromAir = 0
        
        self.windSpeedMagnitude = random.randint(1, 10)
        self.windSpeedAngle = 0
        
        self.sunIntensity = 0
        self.sunlightData = {}
        
        self.graphic = "blank"
        self.graphicOverlay = []
        
        self.type = None


# Holds data for all tiles for min/max/avg calculations
# Subclass to Map
class Value_Lists:
    def __init__(self, mapData, tileCount):
        self.mapData = mapData
        self.tileCount = tileCount
        self.reload()
    def reload(self):
        self.elevation = []
        self.temperature = []
        self.airTemperature = []
        self.airPressure = []
        self.airDensity = []
        self.windSpeedMagnitude = []
        for i in range(self.tileCount):
            rowElevation = []
            rowTemperature = []
            rowAirTemperature = []
            rowAirPressure = []
            rowAirDensity = []
            rowWindSpeedMagnitude = []
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                rowElevation.append(tile.elevation)
                rowTemperature.append(tile.temperature)
                rowAirTemperature.append(tile.airTemperature)
                rowAirPressure.append(tile.airPressure)
                rowAirDensity.append(tile.airDensity)
                rowWindSpeedMagnitude.append(tile.windSpeedMagnitude)
            self.elevation.append(rowElevation)
            self.temperature.append(rowTemperature)
            self.airTemperature.append(rowAirTemperature)
            self.airPressure.append(rowAirPressure)
            self.airDensity.append(rowAirDensity)
            self.windSpeedMagnitude.append(rowWindSpeedMagnitude)


# Holds subclasses representing tile data as well as map dimensions, controls, etc.
class GameMap:

    # Initialize game map
    def __init__(self, gameWindow, graphics, mouse, mapSize, antialiasing=True):
        
        # Initialize display values (not changing)
        self.tileRes = 64
        self.tileCount = mapSize
        self.areaTiles = self.tileCount ** 2
        self.gameWindow = gameWindow
        self.graphics = graphics
        self.mouse = mouse
        self.antialiasing = antialiasing
        
        # Map display controls (changeable)
        self.displayMode = "Surface"
        self.windArrows = False
        self.displaySun = True

        # Sun settings
        self.sunGraphics = {}
        self.sunAzimuth = 0 # 0 to 360 degrees (0 is x=0)
        self.sunAltitude = 0 # 0 to 360 degrees (0 is half of map height)
        
        self.heatFlux = 1.2028 * 10**10 # BTU/hr per square mile from sun before albedo
        self.percentRadAtmos = 0.9
        
        self.stoneHeatCapacity = 0.23885 # BTU/lb F 
        self.waterHeatCapacity = 1.001 # BTU/lb F 
        self.airHeatCapacity = 0.17128 # BTU/lb F
        
        self.stoneMass = 4.795 * 10**10 # lb per volume, 1mi x 1mi x 10ft
        self.waterDensity = 62.4 # lb / ft^3
        self.iceDensity = 57.24644 # lb / ft^3
        
        self.stoneAlbedo = 0.35
        self.waterAlbedo = 0.075
        self.iceAlbedo = 0.75
        self.snowAlbedo = 0.75
        self.atmosAlbedo = 0.3
        
        self.greenhouse = 0.1
        
        self.boltzmann = 0.1714 * 10**-8 # Btu/hr ft2 °R4 ***RANKINE

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
        sizePixels = self.tileRes * self.tileCount
        self.size = Map_Actual_Size(sizePixels)
        self.areaPixels = self.size.x * self.size.y

        # Initialize display size (modified on zoom)
        self.displaySize = Map_Display_Size(self.size.x, self.size.y)

        # Initialize map in screen center
        self.origin = Map_Origin(self.gameWindow.x/2 - self.displaySize.x/2, \
                                 self.gameWindow.y/2 - self.displaySize.y/2)

        # Generate map tile values (initially empty/blank, then algorithm run)
        self.seaLevel = 0
        self.mapData = self.Map_Data(self.tileCount)
        self.rand_gen()
        self.valueList = Value_Lists(self.mapData, self.tileCount)
        self.reset_tiles()
        self.calc_sun()
        self.reset_suntiles()
        
        # Print information to stdout
        Write_Stdout("Map Size: " + str(self.tileCount) + " x " + str(self.tileCount) + " tiles (" + str(self.size.x) + " x " + str(self.size.y) + " px)")
        Write_Stdout("Map Area: " + str(self.areaTiles) + " tiles (" + str(self.areaPixels) + " px)")


    # Subclass for Map to store tile data
    class Map_Data:
        def __init__(self, mapSize):
            # Generate map tile values
            self.tiles = []
            for i in range(mapSize):
                row = []
                for j in range(mapSize):
                    tile = Tile(i, j)
                    row.append(tile)
                self.tiles.append(row)
    
    
    # Scale map values for zoom
    def zoom(self, input):
        zoomFactor = int(input * self.zoomIncrement)
        self.displaySize.x += zoomFactor
        self.displaySize.y += zoomFactor
        self.origin.x -= zoomFactor/2
        self.origin.y -= zoomFactor/2
        self.check_bounds()
        self.scale_map()
        if self.displaySun:
            self.scale_sun_map()
            
            
    # Get initial difference between mouse and origin for click and drag operation
    def click_and_drag_init(self):
        self.mouse.update()
        self.mouseDiff = (self.origin.x - self.mouse.pos[0], self.origin.y - self.mouse.pos[1])


    # Apply changed mouse position (click and drag) to map
    def click_and_drag_update(self):
        self.mouse.update()
        self.origin.x = self.mouse.pos[0] + self.mouseDiff[0]
        self.origin.y = self.mouse.pos[1] + self.mouseDiff[1]
        self.check_bounds()
        
        
    # Reset screen
    def reset_view(self):
        self.displaySize.x = self.size.x
        self.displaySize.y = self.size.y
        self.origin.x = self.gameWindow.x/2 - self.displaySize.x/2
        self.origin.y = self.gameWindow.y/2 - self.displaySize.y/2
        self.check_bounds()


    # Check map zoom/pan meets restrictions
    def check_bounds(self):
    
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


    # Prototype algorithm for world generation
    def rand_gen(self):
    
        seedCount = int(self.areaTiles / 2)
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
        def temperatureCurve(latitude):
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
                temperature = temperatureCurve(latitudeValuePercent)
                airTemperature = temperatureCurve(latitudeValuePercent)
                
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
        for i in range(3):
            self.calc_velocity()
              
              
    # Apply effect to temp, pressure, and density according to tile elevation
    # Values should represent air at whatever elevation is just above surface (incl. ocean surface)
    # Should only apply once !!! after initial value generation (rand_gen)
    def elevation_calcs(self):
    
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

    
    # Adjust temp of tiles (apply sun energy, convection from wind, and conduction from air tile to tile
    def heat_calcs(self):
    
        # Change temp of tiles in sunlight      
        for i in range(self.tileCount):
            for j in range(self.tileCount):
            
                # Get tile elevation data
                tile = self.mapData.tiles[i][j]
                tileType = tile.type
                tileTemperature = tile.temperature
                tileAirTemperature = tile.airTemperature
                tileHeatFromAir = tile.heatFromAir
                tileAirDensity = tile.airDensity
                tileElevation = tile.elevation
                tileTemperatureRankine = tileTemperature + 459.67
                tileAirTemperatureRankine = tileAirTemperature + 459.67
                tileLit = tile.sunlightData[self.sunAzimuth]
                
                airTempElevFactor = self.airTempElevFactor
                
                # Change temp if tile is sunlit
                if tileLit:
                    latitudeFactor = math.sin(math.pi * float(j / self.tileCount)) + 0.5
                    heatAdded = self.heatFlux * latitudeFactor # BTU (if one iteration per hour)         
                else:
                    heatAdded = 0
                    
                # Tile-based heat calc values (material properties)
                if tileType == "stone":
                    surfaceAlbedo = self.stoneAlbedo
                    heatCapacity = self.stoneHeatCapacity
                    surfaceMass = self.stoneMass
                elif tileType == "water":
                    surfaceAlbedo = self.waterAlbedo
                    heatCapacity = self.waterHeatCapacity
                    surfaceMass = self.waterDensity * 5280.0**3
                elif tileType == "snow":
                    surfaceAlbedo = self.snowAlbedo
                    if tileAirTemperature > 32:
                        surfaceAlbedo -= 0.1
                    if tileTemperature > 32:
                        surfaceAlbedo -= 0.15
                    heatCapacity = self.stoneHeatCapacity
                    surfaceMass = self.stoneMass
                elif tileType == "sea_ice":
                    surfaceAlbedo = self.iceAlbedo
                    if tileAirTemperature > 32:
                        surfaceAlbedo -= 0.1
                    if tileTemperature > 32:
                        surfaceAlbedo -= 0.15
                    heatCapacity = self.waterHeatCapacity
                    surfaceMass = self.iceDensity * 5280.0**3
                 
                airMass = (5280.0 ** 3) * tileAirDensity
                 
                # Air to surface convection
                # Convection coefficient maxes out at 120mph wind and 175 W/m^2 K
                airConvCoefBounds = (0.088, 30.840) # 0.5 to 175 W/m^2 K in BTU/ft^2 F
                if tile.windSpeedMagnitude > 176.0: # 120mph -- 176 ft/s
                    airConvectionCoefficient = 1.0
                else:
                    airConvectionCoefficient = tile.windSpeedMagnitude / 176.0
                airConvectionCoefficient = airConvCoefBounds[0] + \
                                         ((airConvCoefBounds[1] - airConvCoefBounds[0]) * airConvectionCoefficient)
                deltaTemp = tileAirTemperature - tileTemperature
                
                # Surface roughness increase on surface area estimation
                # Rougher surface = more surface area for convection
                if tileType == 'stone':
                    roughnessFactor = 1.2
                elif tileType == 'snow':
                    roughnessFactor = 1.5
                else:
                    roughnessFactor = 1
                
                # BTU from (BTU/ft^2 F) * (ft^2) * (degrees F)
                airToSurfaceConvection = (airConvectionCoefficient*roughnessFactor) * (5280**2) * deltaTemp
                 
                # Calculate energy breakdown for surface
                # apply greenhouse factor to percent of sun energy absorbed by atmosphere
                # remaining energy goes to surface
                percentRadAtmos = self.percentRadAtmos * self.greenhouse
                percentRadSurf = 1 - percentRadAtmos
                
                surfaceEnergy = (percentRadSurf * heatAdded) + tileHeatFromAir
                tile.heatFromAir = 0

                # Surface heat transfer
                totalSurfHeatReflected = surfaceEnergy * surfaceAlbedo   
                totalSurfHeatEmitted = self.boltzmann * tileTemperatureRankine**4 * (5280.0**2)
                totalSurfHeatLoss = totalSurfHeatEmitted + totalSurfHeatReflected
                totalSurfHeatAdded = surfaceEnergy - totalSurfHeatLoss + airToSurfaceConvection
                surfDeltaT = totalSurfHeatAdded / (surfaceMass * heatCapacity)
                tile.temperature = tileTemperature + surfDeltaT

                # Calculate energy breakdown for atmosphere, add lost surface energy
                atmosEnergy = (percentRadAtmos * heatAdded) + (totalSurfHeatLoss * self.greenhouse)

                # Atmosphere 
                totalAtmosHeatReflected = atmosEnergy * self.atmosAlbedo   
                totalAtmosHeatEmitted = self.boltzmann * tileAirTemperatureRankine**4 * (5280.0**2)
                totalAtmosHeatLoss = totalAtmosHeatReflected + totalAtmosHeatReflected
                totalAtmosHeatAdded = atmosEnergy - totalAtmosHeatEmitted - airToSurfaceConvection
                atmosDeltaT = totalAtmosHeatAdded / (airMass * self.airHeatCapacity)
                
                tile.heatFromAir = totalAtmosHeatLoss * self.greenhouse

                if atmosDeltaT < 0:
                    airTempElevFactor = 1
                
                # Save previous value to calculate change in pressure/density
                tile.lastAirTemperature = float(tileAirTemperature)
                tile.airTemperature = tileAirTemperature + atmosDeltaT * airTempElevFactor 
                

    # Solve stuff based on tile values
    def calc_velocity(self):
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


    # Change pressure from temperature change
    def gas_calcs(self):
    
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
                


    # Solve stuff based on tile values
    def calc_temp_and_pressure(self):
    
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


    # Update map surface with new data
    def update_map(self):
    
        # Create a surface and pass in a tuple containing its length and width
        self.mapSurface = pygame.Surface((self.size.x, self.size.y))
        self.mapSurface.fill((120, 120, 120))
        for i in range(self.tileCount):
            for j in range(self.tileCount):
                tile = self.mapData.tiles[i][j]
                tileType = tile.graphic
                currentPosition = (i*self.tileRes, j*self.tileRes)
                tileGraphic = self.graphics.data[tileType]
                self.mapSurface.blit(tileGraphic, currentPosition)
                if self.windArrows:
                    arrowImage = self.graphics.data["arrow"]
                    Rotate_Center(self.mapSurface, arrowImage, currentPosition, tile.windSpeedAngle)
                if tile.graphicOverlay != []:
                    for overlay in tile.graphicOverlay:
                        graphicOverlayType = overlay[0]
                        graphicOverlay = self.graphics.data[graphicOverlayType]
                        tileOverlayAngle = overlay[1]
                        Rotate_Center(self.mapSurface, graphicOverlay, currentPosition, tileOverlayAngle)


    # Generate sun map
    def reset_suntiles(self):
    
        # Generate blank map layer
        self.sunLayerSurface = self.sunGraphics[self.sunAzimuth]
        self.scale_sun_map()


    # Sun position & lighting calculation
    # Meant to run once prior to gameplay - calculation done ahead of time and saved as lists in tile data
    def calc_sun(self):

        # Reference graphics
        sunGraphic = self.graphics.data["sun"]
        shadowImage = self.graphics.data["shadow_50percent"]

        # Loop through degrees of azimuth, 1-360
        sunDataResolution = 15 # increments for data loop
        for azimuth in range(0,360,sunDataResolution):

            # Generate blank map layer
            sunLayerSurface = pygame.Surface((self.size.x, self.size.y), pygame.SRCALPHA)
            sunLayerSurface.fill((255, 255, 255, 0))

            # Calculate center location of sun on map
            dieoutFactor = 1.475
            
            halfTileCount = float(self.tileCount) / 2.0
            sunPositionY = halfTileCount + (self.sunAltitude / 90) * halfTileCount
            sunPositionX = float(self.tileCount) * (azimuth / 360.0)
            sunPosition = (sunPositionX * self.tileRes, sunPositionY * self.tileRes)
            sunLayerSurface.blit(sunGraphic, sunPosition)

            # Latitude factors calculated based on Mercator Projection (1/cos(lat))
            latitudeFactorBase = 1.0 / math.cos(math.radians(self.sunAltitude / dieoutFactor))

            # Calculate base dimensions of sunlit area on map
            sunlightWidthBase = float(self.tileCount) / 4.0
            sunlightWidth = sunlightWidthBase * latitudeFactorBase
            sunlightHeight = float(self.tileCount) / 2.0
            
            # Loop by latitude first (j index or y location) as scale factor is calculated on that basis
            for j in range(self.tileCount):
                if j < halfTileCount:
                    heightIndex = j+1
                else:
                    heightIndex = j
                latitudeFactor = 1.0 / math.cos(math.radians(((abs(halfTileCount - heightIndex) / halfTileCount) * 90.0) / dieoutFactor))
                latFactorAdjusted = latitudeFactor / latitudeFactorBase
                latAdjustedWidth = sunlightWidth * latFactorAdjusted
                sunBounds = (sunPositionX - latAdjustedWidth, sunPositionX + latAdjustedWidth)
                if sunBounds[0] < 0 and sunBounds[1] > self.tileCount:
                    sunBoundsAdj = [(0, self.tileCount), (0, self.tileCount)]
                elif sunBounds[0] < 0:
                    sunBoundsAdj = [(0, sunBounds[1]), (self.tileCount - abs(sunBounds[0]), self.tileCount)]
                elif sunBounds[1] > self.tileCount:
                    sunBoundsAdj = [(0, abs(sunBounds[1]) - self.tileCount), (sunBounds[0], self.tileCount)]     
                else:
                    sunBoundsAdj = [sunBounds, sunBounds]
                for i in range(self.tileCount):
                    lengthIndex = i
                    currentPosition = (i*self.tileRes, j*self.tileRes)
                    if not ((lengthIndex >= sunBoundsAdj[0][0] and lengthIndex <= sunBoundsAdj[0][1]) or \
                            (lengthIndex >= sunBoundsAdj[1][0] and lengthIndex <= sunBoundsAdj[1][1])):
                        self.mapData.tiles[i][j].sunlightData.update({azimuth: False})
                        sunLayerSurface.blit(shadowImage, currentPosition)
                    else:
                        self.mapData.tiles[i][j].sunlightData.update({azimuth: True})
                    
            self.sunGraphics.update({azimuth: sunLayerSurface})


    # Run whenever tiles are updated
    # Applies graphics to tiles
    def reset_tiles(self):
    
        #self.valueList.reload()
        
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
                        
        elif self.displayMode == "Elevation Ground-Only":
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
                    tileX = i * self.tileRes
                    tileY = j * self.tileRes
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
        

    # Scale function
    def scale_map(self):
        if self.antialiasing is True:
            self.mapSurfaceScaled = pygame.transform.smoothscale(self.mapSurface, (self.displaySize.x, self.displaySize.y))
        else:
            self.mapSurfaceScaled = pygame.transform.scale(self.mapSurface, (self.displaySize.x, self.displaySize.y))


    # Scale function
    def scale_sun_map(self):
        if self.antialiasing is True:
            self.sunLayerSurfaceScaled = pygame.transform.smoothscale(self.sunLayerSurface, (self.displaySize.x, self.displaySize.y))
        else:
            self.sunLayerSurfaceScaled = pygame.transform.scale(self.sunLayerSurface, (self.displaySize.x, self.displaySize.y))


    # Return map surface for blit
    def get_map(self):
        return self.mapSurfaceScaled, (self.origin.x, self.origin.y)


    # Return sun map layer/surface for blit
    def get_sun_map(self):
        return self.sunLayerSurfaceScaled, (self.origin.x, self.origin.y)
