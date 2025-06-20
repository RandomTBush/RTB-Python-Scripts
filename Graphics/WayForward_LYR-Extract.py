import os
import sys
import platform
import glob
import struct
from PIL import Image

# WayForward GBA/DS/LeapFrog Didj/Leapster screen / map (*.LYR) extraction script written by Random Talking Bush.
# Based only slightly on onepill's TextureUnpacker script: https://github.com/onepill/texture_unpacker_scirpt

LYRFormat = 0 # See the list below for which value should be used for the game you're ripping from.
MetatilesName = "BrambleMaze" # PNG exported from my "WayForward_TS-Extract" script, minus the "_metatile" suffix. If a PNG matching the .LYR's internal tileset ID is autodetected (such as "311_metatile.png", useful for pairing GBA .LYR files), that will be used instead.
ScreenName = "366" # Filename of .LYR file, minus extension. Ignored when UseGBAROM is True. (Example: "366" will be the first foreground layer of the Bramble Maze when using my QuickBMS script to unpack Shantae Advance: Risky Revolution.)

UseGBAROM = False # Change this to true to read from a GBA ROM instead of a .LYR file. Make sure both the "ROMName" and "ScreenStart" lines below are filled in correctly.
ROMName = "Shantae.gba" # GBA ROM file needed to extract map data. Ignored when UseGBAROM is False.
ScreenStart = 0x96B074 # Offset to the start of the screen data in a GBA ROM. Ignored when UseGBAROM is False. (Example: "0x96B074" will be the first foreground layer of the Bramble Maze in Shantae Advance: Risky Revolution.)

# Instructions on how to use this script:
# 1. Install both Python (either 2 or 3, both work) and Pillow: https://github.com/python-pillow/Pillow
# 2. If ripping from a GBA game, use QuickBMS (https://aluigi.altervista.org/quickbms.htm) and one of my "WayForwardGBA" scripts (https://github.com/RandomTBush/RTB-QuickBMS-Scripts/tree/master/Archive) to unpack the game you want to rip from. For DS or Didj games, you can use something like Tinke to unpack the former and 7-Zip for the latter.
# 3. Use my "WayForward_TS-Extract" script first to set up the "metatile" sheet (the included "BrambleMaze_metatile" and "scuttletown_pf_metatile" samples from Shantae Advance and Risky's Revenge respectively should give you an example of what you're looking for).
# 4. For a .LYR file, set the UseGBAROM option to False. Change the path for the "ScreenName" entry above to the name of the .LYR file you want to extract (if UseGBAROM = False, otherwise see the section below), and the "MetatilesName" with the name of the metatile image generated with step #3.
# 5. With the previous steps done, run the script (no additional command-line parameters needed). If everything's ret-2-go, then resulting screens plus an assembled map will be in a subfolder with the same name as the .LYR file (if UseGBAROM = False) or the ROM offset (if UseGBAROM = True).

# ROM-file ripping (for experts):
# 4B. Set the UseGBAROM option to True, change the name for the "ROMName" entry to match the GBA ROM you want to try extracting a screen / map file from (eg. "Shantae.gba", it can either be a relative name or a full path), and the "MetatilesName" entry to the name of the extracted metatiles PNG (see step #3 in the previous section).
# 4C. Locate the start of the screen information in the GBA ROM. It's harder to explain compared to the .ANM sprites and .TS4/.TS8 tilesets, so just look at the example offset above for Shantae Advance or any other .LYR files to get a general idea of what you're looking for there, and fill in the "ScreenStart" value above accordingly.

# Troubleshooting:
# If the script throws an error or doesn't export anything, check to make sure that the "LYRFormat", "MetatilesName" and "ScreenName" entries are filled in correctly. If UseGBAROM = True, double-check in a hex editor to make sure you have the right offset set up for "ScreenStart" (it tends to start with 0x0000, 0x0010, 0x0020 or 0x0040), and ends in either 0, 4, 8 or C. Shift it forward or backward by 4 at a time if you need to.
# If the exported screen tiles seem garbled, either your metatiles image is set up incorrectly, you have the wrong offset listed in "ScreenStart" (see above).

# Works with the following games:
# --------------------------------------------------------------------------------
# Game Boy Advance:
# American Dragon: Jake Long - Rise of the Huntsclan        [Set LYRFormat = 3]
# Barbie and the Magic of Pegasus                           [Set LYRFormat = 3]
# Barbie in the 12 Dancing Princesses                       [Set LYRFormat = 3]
# Barbie: The Princess and the Pauper                       [Set LYRFormat = 1]
# Godzilla: Domination                                      [Set LYRFormat = 1]
# Justice League Heroes: The Flash                          [Set LYRFormat = 3]
# Looney Tunes: Double Pack - Dizzy Driving / Acme Antics   [Set LYRFormat = 2]
# Rescue Heroes: Billy Blazes                               [Set LYRFormat = 1]
# The Scorpion King: Sword of Osiris                        [Set LYRFormat = 0]
# Sigma Star Saga                                           [Set LYRFormat = 3]
# Shantae Advance: Risky Revolution                         [Set LYRFormat = 2]
# Shantae Advance: Risky Revolution (Battle Mode)           [Set LYRFormat = 1]
# Shantae Advance: Risky Revolution (Demo)                  [Set LYRFormat = 1]
# SpongeBob SquarePants: Creature from the Krusty Krab      [Set LYRFormat = 3]
# SpongeBob SquarePants: Lights, Camera, Pants!             [Set LYRFormat = 3]
# The SpongeBob SquarePants Movie                           [Set LYRFormat = 1]
# Tak: The Great Juju Challenge                             [Set LYRFormat = 3]
# Unfabulous!                                               [Set LYRFormat = 3]
# X-Men: The Official Game                                  [Set LYRFormat = 3]
# --------------------------------------------------------------------------------
# DS/DSi [All games use LYRFormat = 3]:
# Aliens: Infestation
# American Dragon: Jake Long - Attack of the Dark Dragon
# Barbie and the Three Musketeers
# Barbie in the 12 Dancing Princesses
# Batman: The Brave and the Bold
# Contra 4
# Despicable Me: Minion Mayhem
# Galactic Taz Ball
# Looney Tunes: Duck Amuck
# Mighty Flip Champs
# Mighty Milky Way
# Shantae: Risky's Revenge
# Shrek: Ogres & Dronkeys
# Space Chimps
# SpongeBob SquarePants: Creature from the Krusty Krab
# Thor: God of Thunder
# Where the Wild Things Are
# --------------------------------------------------------------------------------
# LeapFrog Didj [Both games use LYRFormat = 3]:
# Nicktoons: Android Invasion
# SpongeBob SquarePants: Fists of Foam
# --------------------------------------------------------------------------------
# LeapFrog Leapster [All games use LYRFormat = 2]:
# Cosmic Math
# Letterpillar
# Number Raiders
# The Batman: Multiply, Divide and Conquer
# The Batman: Strength in Numbers
# Word Chasers
# --------------------------------------------------------------------------------
# Everything below this line should be left alone.

if UseGBAROM == False:
    if not os.path.exists(ScreenName + ".lyr"):
        print("Can't find '" + ScreenName + ".lyr'. Check to make sure you filled in the 'ScreenName' entry correctly.")
        os.system('pause')
        exit()
    else:
        scrfile = open(ScreenName + '.lyr', "rb") # .LYR file
        scrfile.seek(0, 0) # Start at the top of the .LYR file.
        if not os.path.exists(ScreenName):
            os.makedirs(ScreenName) # If the folder doesn't exist, then make it.
else:
    if not os.path.exists(ROMName):
        print("Can't find " + ROMName + ". Check to make sure you filled in the 'ROMName' entry correctly.")
        os.system('pause')
        exit()
    else:
        scrfile = open(ROMName, "rb") # .GBA ROM file
        scrfile.seek(ScreenStart, 0) # Start at the "ScreenStart" offset above.
        if not os.path.exists(str(ScreenStart)):
            os.makedirs(str(ScreenStart)) # We'll use the offset as the folder name for Risky Revolution.

ScreenFlags = struct.unpack('<H', scrfile.read(2))[0] # Flags. 0x0010, 0x0020 and 0x0040 exist. TODO: Figure out the context of 0x0020.
ScreenWidth = struct.unpack('<H', scrfile.read(2))[0] # How many screens wide is the map.
ScreenHeight = struct.unpack('<H', scrfile.read(2))[0] # How many screens tall is the map.
ScreenCount = struct.unpack('<H', scrfile.read(2))[0] # How many unique screens are in the map. First screen is always blank, so two is technically the minimum unless it's empty.
if LYRFormat == 0:
    ScreenUnkA = struct.unpack('<H', scrfile.read(2))[0] # Count?
    ScreenTypesID = struct.unpack('<H', scrfile.read(2))[0] # File number of "TYPES.TYP".
    ScreenTilesetID = struct.unpack('<H', scrfile.read(2))[0] # File number of the tileset used.
    ScreenUnkD = struct.unpack('<H', scrfile.read(2))[0] # Always 0xCCCC?
elif LYRFormat == 1:
    ScreenUnkA = struct.unpack('<H', scrfile.read(2))[0] # ???
    ScreenTypesID = struct.unpack('<H', scrfile.read(2))[0] # File number of "TYPES.TYP".
    ScreenUnkC = struct.unpack('<H', scrfile.read(2))[0] # ???
    ScreenTilesetID = struct.unpack('<H', scrfile.read(2))[0] # File number of the tileset used.
else:
    ScreenUnkCountA = struct.unpack('<H', scrfile.read(2))[0] # ???
    ScreenUnkCountB = struct.unpack('<H', scrfile.read(2))[0] # ???
    ScreenUnkCountC = struct.unpack('<H', scrfile.read(2))[0] # ???
    ScreenTypesID = struct.unpack('<H', scrfile.read(2))[0] # File number of "TYPES.TYP".
    ScreenUnkIDB = struct.unpack('<H', scrfile.read(2))[0] # ???
    ScreenTilesetID = struct.unpack('<H', scrfile.read(2))[0] # File number of the tileset used.

if not os.path.exists(str(ScreenTilesetID) + '_metatile.png'):
    if not os.path.exists(MetatilesName + '_metatile.png'):
        print("Can't find metatile image '" + MetatilesName + "_metatile.png'. Run the 'WayForward_TS-Extract' script to generate one first, or correct the 'MetatilesName' entry if you already did.")
        os.system('pause')
        exit()
    else:
        sprfile = Image.open(MetatilesName + '_metatile.png') # Open the metatiles file which matches the "MetatilesName" entry above.
else:
    sprfile = Image.open(str(ScreenTilesetID) + '_metatile.png') # Override the "MetatilesName" entry above if it finds a matching ID. Helpful for GBA games.
    print("Found tileset matching internal ID ('" + str(ScreenTilesetID) + "_metatile.png') using that instead.")

ScreenIDRet = scrfile.tell()
for x in range(ScreenWidth * ScreenHeight):
    ScreenID = struct.unpack('<H', scrfile.read(2))[0] # Which 256x256 screen is used for this section of the map.
if LYRFormat == 0:
    if scrfile.tell() % 4 != 0:
        print("Re-aligning...")
        scrfile.seek(2, 1) # Screen data has to start at an offset which is a multiple of 4 (*0, *4, 8, or *C) for The Scorpion King, so re-align if it's not (it'll never end on an odd number, so shift by 2 will work).
if LYRFormat > 2:
    for x in range(ScreenWidth * ScreenHeight):
        ScreenID2 = struct.unpack('<H', scrfile.read(2))[0] # A secondary set of IDs which don't seem necessary for map building.
    for x in range(ScreenWidth * ScreenHeight):
        ScreenID3 = struct.unpack('<H', scrfile.read(2))[0] # And a third that's not needed.
    scrfile.seek((ScreenUnkCountA * 20), 1) # Skip past the first set of unknowns...
    scrfile.seek((ScreenUnkCountB * 8), 1) # ...and the second...
    scrfile.seek((ScreenUnkCountC * 16), 1) # ...and the third.

for x in range(ScreenCount):
    MetatileStartX = 0; MetatileStartY = 0; MetatilePasteX = 0; MetatilePasteY = 0 # Initializing values for screen assembly.
    ScreenImage = Image.new('RGBA', (256, 256), (0, 0, 0, 0)) # Initializing the assembled screen PNG in memory.
    for y in range(256):
        MetatileID = struct.unpack('<H', scrfile.read(2))[0] # Which metatile is used for this offset. Screens are always 16x16 metatiles, or 256x256.
        if ScreenFlags == 0x0010:
            MetatileID = MetatileID & 0x03FF # 1024 metatiles maximum?
            MetatileStartX = (MetatileID & 0x000F) * 16 # Maths to determine X position of metatile sheet to cut.
            MetatileStartY = (MetatileID & 0x03F0) # More maths to determine Y position of metatile sheet to cut.
        elif ScreenFlags == 0x0040:
            MetatileID = MetatileID & 0x0FFF # 4096 metatiles maximum.
            MetatileStartX = (MetatileID & 0x000F) * 16 # Maths to determine X position of metatile sheet to cut.
            MetatileStartY = (MetatileID & 0x0FF0) # More maths to determine Y position of metatile sheet to cut.
        else:
            MetatileID = MetatileID & 0x07FF # 2048 metatiles maximum, presumably.
            MetatileStartX = (MetatileID & 0x000F) * 16 # Maths to determine X position of metatile sheet to cut.
            MetatileStartY = (MetatileID & 0x07F0) # More maths to determine Y position of metatile sheet to cut.
        CropImage = sprfile.crop((MetatileStartX, MetatileStartY, MetatileStartX + 16, MetatileStartY + 16)) # Grabbing the right metatile.
        ScreenImage.paste(CropImage, ((MetatilePasteX * 16), (MetatilePasteY * 16)), mask=0) # Pasting the metatile in the right spot.
        MetatilePasteX = MetatilePasteX + 1 # Shift right by 1 metatile.
        if MetatilePasteX == 16:
            MetatilePasteX = 0 # We've reached the edge, so we reset and...
            MetatilePasteY = MetatilePasteY + 1 # ...move onto the next line.

    if UseGBAROM == False:
        outfile = (ScreenName + '/' + str(x) + '.png') # Setting up the file path. .LYR files will use their name for the folder.
    else:
        outfile = (str(ScreenStart) + '/' + str(x) + '.png') # Setting up the file path. A GBA ROM will use the offset as the name for the folder.
    ScreenImage.save(outfile) # Saving the file.
    print("Saved to " + outfile) # We did the thing.

scrfile.seek(ScreenIDRet, 0) # Now let's try building the entire map...
MetatilePasteX = 0; MetatilePasteY = 0 # Re-initializing values for screen assembly.
MapImage = Image.new('RGBA', ((ScreenWidth * 256), (ScreenHeight * 256)), (0, 0, 0, 0)) # Initializing the full map PNG in memory.

print("Building full map (" + str(ScreenWidth) + "x" + str(ScreenHeight) + ") screens...")
for x in range(ScreenWidth * ScreenHeight):
    ScreenID = struct.unpack('<H', scrfile.read(2))[0] # Which 256x256 screen is used for this section of the map.
    if UseGBAROM == False:
        ScreenTile = Image.open(ScreenName + '/' + str(ScreenID) + '.png') # Get the respective screen from the "ScreenName" folder.
    else:
        ScreenTile = Image.open(str(ScreenStart) + '/' + str(ScreenID) + '.png') # Get the respective screen from the "ScreenStart" folder.
    MapImage.paste(ScreenTile, ((MetatilePasteX * 256), (MetatilePasteY * 256)), mask=0) # Pasting the screen in the right spot, but only if it's not blank.
    MetatilePasteX = MetatilePasteX + 1 # Shift right by 1 metatile.
    if MetatilePasteX == ScreenWidth:
        MetatilePasteX = 0 # We've reached the edge, so we reset and...
        MetatilePasteY = MetatilePasteY + 1 # ...move onto the next line.

if UseGBAROM == False:
    outfile = (ScreenName + '/' + 'Full.png') # Setting up the full map file path, will use the .LYR's name for the folder.
else:
    outfile = (str(ScreenStart) + '/' + 'Full.png') # Setting up the full map file path, will use the ROM's offset as the name for the folder.
MapImage.save(outfile) # Saving the assembled map.
print("Saved to " + outfile) # We did the other thing.