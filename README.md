# ANTISTASIS
This is an amateur game that likely will not be finished any time in the near future.
The code uploaded on 12/19/2024 was almost entirely developed in 2022, besides maybe a few small changes.

## OBJECTIVE
This game aims to be closer to a simulation than a traditional game, exploring the intersection of climate, nature, and human civilization.
The ultimate goal will be gameplay where the player can take the role of either nature or humanity, and either destroy the other or learn to coexist.

## CURRENT STATE
12/19/2024:
Using Python/Pygame, the current game is a map generator and a barely-functioning, inefficient simulation of heat transfer.
The near-term goal is to move to Pyglet and improve code efficiency and readability. 
The mid-term goal is to have *at least* the climate simulation layer functioning as well as it can, identifying the capabilities of the simulation (i.e. world size).
The long-term goal is to move to another language entirely, refactoring the code to work in a better environment like Unity or Godot.

## DESCRIPTION
The current game process simplified...
1. Generate a world of size X-by-Y, where each discrete coordinate is a "tile", or a 1 mile x 1 mile square.
   The top and bottom of the world represent the poles of a spherical planet. Each tile also has "air", another layer that has implications on the simulation.
3. Generate topography, using randomness and math to set the "elevation" of each tile, apparent in the main game view.
   Elevation values below a certain threshold (default 0) are considered ocean, also apparent in the main game view.
4. Generate initial temperature profile, with colder values at the poles and warmer at the equator (center of map).
5. Initial elevation, temperature, and whether land is ocean, stone (warm land above sea-level), or ice (ocean or land below freezing) has bearing on simulation.
   Each tile type has different heat capacity, albedo, etc.
6. Dependent on the physical properties, time of day, etc., once the game is unpaused, the game starts to "tick" - one hour per tick.
   Each tick runs a calculation on each tile, calculating radiation from the sun based on latitude/albedo, convection from air to land, and (eventually) air-to-air.
   This means cold, icy land doesn't heat as quick due to reflection of sun radiation and angle of incidence.
   Land heated to above freezing becomes more absorptive and heats up quicker.
