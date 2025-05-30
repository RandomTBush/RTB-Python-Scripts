import os
import sys
import platform
import glob
import struct
from PIL import Image, ImagePalette

# WayForward GBA/DS/LeapFrog Didj sprite animation (*.ANM/*.AN4/*.AN8) extraction script written by Random Talking Bush.
# Based only slightly on onepill's TextureUnpacker script: https://github.com/onepill/texture_unpacker_scirpt

ANMFormat = 0 # See the list below for which value should be used for the game you're ripping from. Actual "version" ordering is 1 > 2 > 0 > 3 > 4 > 5, "0" was made the default due to being the most common.
SpriteName = "20" # The name of the .ANM, .AN4 or .AN8 file, will also be the name of the folder said sprites will extract to. Ignored if UseGBAROM = True (it will use the "SpriteStart" offset instead). (Example: "20" will be Shantae's .ANM filename when using my QuickBMS script to unpack Shantae Advance: Risky Revolution.)
SceneName = "419" # The name of the .SCN or .PAL file to use the palette from, minus extension. Leave blank to use a grayscale palette.
PaletteNum = 1 # Use the specified palette number (from 0-15) for the exported sprites. If the sprites look off, change this number and re-export. Ignored if sprites are 8BPP / 256-colour.
SpriteWidth = 256 # Change this and/or the next value to adjust the image dimensions of the sprite output.
SpriteHeight = 256 # You will need to set this to a higher amount such as 384 for some of the larger sprites, or else they'll be cropped off at the edges. 256 is more than enough for most of them.
TileBounds = False # Set this to True to use a transparent canvas for the extracted sprites instead of limiting them to their 256-colour palettes, exposing the tile edges in the process.

UseGBAROM = False # Change this to True to read from a GBA ROM instead of a .ANM file. Make sure both the "ROMName" and "SpriteStart" lines below are filled in correctly. For experts only -- you're better off using my QuickBMS scripts to unpack the ROM files instead.
ROMName = "Shantae.gba" # Game Boy Advance ROM file needed to extract sprite data. Ignored when UseGBAROM is False (it uses the "SpriteName" above instead).
SpriteStart = 0x34E368 # Offset to the start of animation data in a GBA ROM, located at the very beginning of the "garbage" data for the respective sprite set. Ignored when UseGBAROM is False. (Example: 0x34E368 is the offset to Shantae's .ANM file in Shantae Advance: Risky Revolution.)

# Instructions on how to use this script:
# 1. Install both Python (either 2 or 3, both work) and Pillow: https://github.com/python-pillow/Pillow
# 2. If ripping from a GBA game, use QuickBMS (https://aluigi.altervista.org/quickbms.htm) and one of my "WayForwardGBA" scripts (https://github.com/RandomTBush/RTB-QuickBMS-Scripts/tree/master/Archive) to unpack the game you want to rip from. For DS or Didj games, you can use something like Tinke to unpack the former and 7-Zip for the latter.
# 3. For a .ANM file, set the UseGBAROM option to False. Change the path for the "SpriteName" entry above to the name of the .ANM file you want to extract (if UseGBAROM = False, otherwise see the section below), and the "SceneName" to the scene / palette file you want to use for the exported sprites.
# 4. Run the script (no additional command-line parameters needed). If everything's ret-2-go, then resulting sprites can be found in the subfolder named after the "SpriteName" above. Change the "PaletteNum" value or try another scene / palette file if the sprites have the wrong palette applied.

# ROM-file ripping (for experts):
# 3B. Set the UseGBAROM option to True, change the name for the "ROMName" entry to match the GBA ROM you want to try extracting sprites from (eg. "Shantae.gba", it can either be a relative name or a full path).
# 3C. Locate the assembly information for the respective sprite set in the GBA ROM, which has the visual appearance of random pixels scattered about and is always located above the sprite tiles (not below). At the very top of the "thinner" set and immediately following the tiles of the previous sprite set should be the offset you want to fill in for the "SpriteStart" value above.

# Troubleshooting:
# If the sprites have the wrong palette, change the "PaletteNum" value and re-export, as stated above.
# If the script throws an error or doesn't export anything, check to make sure that you have the right "ANMFormat" and "SpriteName" values filled in. 
# If extracting from a GBA ROM instead of a .ANM file, make sure that the "SpriteStart" offset ends in either 0, 4, 8 or C, double-check in a hex editor to make sure you're in the right spot if you need to. Sprite assembly data starts with something similar to "00 00 05 00" with only the third byte being non-zero, and 16 bytes ahead of that should be "00 00 00 00" for the most common .ANM formats. Shift it forward or backward by 4 at a time if you need to.

# Works with the following games:
# --------------------------------------------------------------------------------
# Game Boy Advance:
# American Dragon: Jake Long - Rise of the Huntsclan        [Set ANMFormat = 0]
# Barbie and the Magic of Pegasus                           [Set ANMFormat = 0]
# Barbie in the 12 Dancing Princesses                       [Set ANMFormat = 0]
# Barbie: The Princess and the Pauper                       [Set ANMFormat = 0]
# Godzilla: Domination                                      [Set ANMFormat = 0]
# Justice League Heroes: The Flash                          [Set ANMFormat = 0]
# Looney Tunes: Double Pack - Dizzy Driving / Acme Antics   [Set ANMFormat = 0]
# Rescue Heroes: Billy Blazes                               [Set ANMFormat = 2]
# The Scorpion King: Sword of Osiris                        [Set ANMFormat = 1]
# Sigma Star Saga                                           [Set ANMFormat = 0]
# Shantae Advance: Risky Revolution                         [Set ANMFormat = 0]
# Shantae Advance: Risky Revolution (Battle Mode)           [Set ANMFormat = 2]
# SpongeBob SquarePants: Creature from the Krusty Krab      [Set ANMFormat = 0]
# SpongeBob SquarePants: Lights, Camera, Pants!             [Set ANMFormat = 0]
# The SpongeBob SquarePants Movie                           [Set ANMFormat = 0]
# Tak: The Great Juju Challenge                             [Set ANMFormat = 0]
# Unfabulous!                                               [Set ANMFormat = 0]
# X-Men: The Official Game                                  [Set ANMFormat = 0]
# --------------------------------------------------------------------------------
# DS/DSi:
# Aliens: Infestation                                       [Set ANMFormat = 3]
# American Dragon: Jake Long - Attack of the Dark Dragon    [Set ANMFormat = 0]
# Barbie and the Three Musketeers                           [Set ANMFormat = 3]
# Barbie in the 12 Dancing Princesses                       [Set ANMFormat = 0]
# Batman: The Brave and the Bold                            [Set ANMFormat = 4]
# Contra 4                                                  [Set ANMFormat = 3]
# Despicable Me: Minion Mayhem                              [Set ANMFormat = 3]
# Galactic Taz Ball                                         [Set ANMFormat = 3]
# Looney Tunes: Duck Amuck                                  [Set ANMFormat = 0]
# Mighty Flip Champs                                        [Set ANMFormat = 3]
# Mighty Milky Way                                          [Set ANMFormat = 4]
# Shantae: Risky's Revenge                                  [Set ANMFormat = 4]
# Shrek: Ogres & Dronkeys                                   [Set ANMFormat = 3]
# Space Chimps                                              [Set ANMFormat = 3]
# SpongeBob SquarePants: Creature from the Krusty Krab      [Set ANMFormat = 0]
# Thor: God of Thunder                                      [Set ANMFormat = 4]
# Where the Wild Things Are                                 [Set ANMFormat = 3]
# --------------------------------------------------------------------------------
# LeapFrog Didj:
# Nicktoons: Android Invasion                               [Set ANMFormat = 5]
# SpongeBob SquarePants: Fists of Foam                      [Set ANMFormat = 5]
# --------------------------------------------------------------------------------
# Everything below this line should be left alone.

if PaletteNum < 0 or PaletteNum > 15:
    print("Invalid 'PaletteNum' value. Make sure it's set to a number within the 0-15 range.")
    exit()

if UseGBAROM == False:
    SpriteStart = 0x0 # Zeroing out the offset, as .ANM/.AN4/.AN8 files have it at the beginning.
    if not os.path.exists(SpriteName + ".anm"):
        if not os.path.exists(SpriteName + ".an4"):
            if not os.path.exists(SpriteName + ".an8"):
                print("Can't find '" + SpriteName + ".anm', '" + SpriteName + ".an4' or '" + SpriteName + ".an8'. Check to make sure you filled in the 'SpriteName' entry correctly.")
                os.system('pause')
                exit()
            else:
                anmfile = open(SpriteName + ".an8", "rb") # Opens a .AN8 file, uses the name listed in "SpriteName" above.
        else:
            anmfile = open(SpriteName + ".an4", "rb") # Opens a .AN4 file, uses the name listed in "SpriteName" above.
    else:
        anmfile = open(SpriteName + ".anm", "rb") # Opens a .ANM file, uses the name listed in "SpriteName" above.
        
else:
    if not os.path.exists(ROMName):
        print("Can't find " + ROMName + ". Check to make sure you filled in the 'ROMName' entry correctly.")
        os.system('pause')
        exit()
    else:
        anmfile = open(ROMName, "rb") # Opens a ROM file needed to extract assembly data, see the above note for the "SpriteStart" offset.

if UseGBAROM == False and ANMFormat == 5:
    # LeapFrog Didj has a 0x200 palette block at the beginning of its .ANM files, which is considered part of the file for its offset calculations.
    print("Didj format tileset, using internal palette.")
    anmfile.seek(0, 0) # Start reading the .ANM file.
    ANMPalette = bytearray()
    # I am doing it this way for the sake of "raw" palettes.
    for x in range(256):
        PaletteBytes = struct.unpack('<H', anmfile.read(2))[0]
        PaletteByteA = ((PaletteBytes & 0x001F)) * 8
        PaletteByteB = ((PaletteBytes & 0x03E0) >> 5) * 8
        PaletteByteC = ((PaletteBytes & 0x7C00) >> 10) * 8
        ANMPalette.append(PaletteByteA)
        ANMPalette.append(PaletteByteB)
        ANMPalette.append(PaletteByteC)
else: 
    anmfile.seek(SpriteStart, 0) # Start reading the .ANM / ROM file.
    if os.path.exists(SceneName + ".pal") or os.path.exists(SceneName + ".scn"):
        if os.path.exists(SceneName + ".pal"):
            scnfile = open(SceneName + ".pal", "rb") # Opens a .PAL file to extract palette information from.
            scnfile.seek(0, 0) # Sprite palettes are in the latter half of the SCN file.
        elif os.path.exists(SceneName + ".scn"):
            scnfile = open(SceneName + ".scn", "rb") # Opens a .SCN file to extract palette information from.
            scnfile.seek(0x200, 0) # Sprite palettes are in the latter half of the SCN file.
        ANMPalette = bytearray()
        # I am doing it this way for the sake of "raw" palettes.
        for x in range(256):
            PaletteBytes = struct.unpack('<H', scnfile.read(2))[0]
            PaletteByteA = ((PaletteBytes & 0x001F)) * 8
            PaletteByteB = ((PaletteBytes & 0x03E0) >> 5) * 8
            PaletteByteC = ((PaletteBytes & 0x7C00) >> 10) * 8
            ANMPalette.append(PaletteByteA)
            ANMPalette.append(PaletteByteB)
            ANMPalette.append(PaletteByteC)
    else:
        if SceneName == "":
            print("Defaulting to grayscale palette.")
        else:
            print("Couldn't find '" + SceneName + ".scn' or '" + SceneName + ".pal', defaulting to grayscale instead.")
        ANMPalette = bytearray() # Forcing a grayscale palette for Python 3 compatibility.
        for x in range(256):
            ANMPalette.append(x) 
            ANMPalette.append(x)
            ANMPalette.append(x)

FrameOffset = {}; FrameStart = {}; FrameLength = {} # Initializing the arrays...
if UseGBAROM == False and ANMFormat == 5:
    anmfile.seek(512, 0) # LeapFrog Didj has a 0x200 palette block at the beginning of its .ANM files, which is considered part of the file for its offset calculations.
else: 
    anmfile.seek(SpriteStart, 0) # And now we start reading the .ANM / ROM file.
FrameFlags = struct.unpack('<H', anmfile.read(2))[0] # 0x0000 (16-colour) and 0x8000 (256-colour), or 0x0F00 (16-colour) and 0xFF00 (256-colour).
FrameMaxPieces = struct.unpack('<H', anmfile.read(2))[0] # a.k.a "wObjMax". Most amount of pieces used for a single frame.
FrameMaxBytes = struct.unpack('<H', anmfile.read(2))[0] # a.k.a "wSizeMax". Most amount of bytes used for a single frame's tiles.
FrameTotal = struct.unpack('<H', anmfile.read(2))[0] # a.k.a "wFrameCount". How many frames for the respective sprite set.
if ANMFormat == 1:
    anmfile.seek(8, 1) # The Scorpion King has two extra sets of bytes in its header.
SpriteTileStart = (struct.unpack('<L', anmfile.read(4))[0] + SpriteStart) # Relative position from the "SpriteStart" value above (or 0 for a .ANM file) where the tile graphics start.
SpriteTileSize = struct.unpack('<L', anmfile.read(4))[0] # Total amount of bytes taken up by the tile graphics.

if UseGBAROM == True:
    if not os.path.exists(str(SpriteStart)):
        os.makedirs(str(SpriteStart)) # If the folder doesn't exist, then make it.
else:
    if not os.path.exists(SpriteName):
        os.makedirs(SpriteName) # If the folder doesn't exist, then make it.

if ANMFormat != 1:
    for x in range(FrameTotal):
        FrameOffset[x] = (struct.unpack('<L', anmfile.read(4))[0] + SpriteStart) # Relative position from the "SpriteStart" value above (or 0 for a .ANM file) for the sprite's tile assembly information.
        FrameStart[x] = struct.unpack('<L', anmfile.read(4))[0] + SpriteTileStart # Add to the "SpriteTileStart" value above for the start of the sprite's tiles.
        FrameLength[x] = struct.unpack('<L', anmfile.read(4))[0] # How many bytes used for the entire sprite's tiles. Not used by the script, but tracked anyway.
else:
    for x in range(FrameTotal):
        FrameOffset[x] = (struct.unpack('<L', anmfile.read(4))[0] + SpriteStart) # The Scorpion King stores these in three separate buffers.
    for x in range(FrameTotal):
        FrameStart[x] = struct.unpack('<L', anmfile.read(4))[0] + SpriteTileStart # Add to the "SpriteTileStart" value above for the start of the sprite's tiles.
    for x in range(FrameTotal):
        FrameLength[x] = struct.unpack('<H', anmfile.read(2))[0] # How many bytes used for the entire sprite's tiles. Not used by the script, but tracked anyway.

for x in range(FrameTotal):
    PivotX = {}; PivotY = {}; TileStart = {}; PieceSize = {}; TileWidth = {}; TileHeight = {} # More array initialization.
    anmfile.seek(FrameOffset[x], 0) # Jump to the next frame for assembly.
    if ANMFormat == 1:
        anmfile.seek(16, 1) # The Scorpion King has tiny buffers.
    elif ANMFormat == 3 or ANMFormat == 5:
        anmfile.seek(32, 1) # Certain DS games and Didj games have an extra 8 bytes.
    elif ANMFormat == 4:
        anmfile.seek(56, 1) # ...while other DS games have an extra 32 bytes instead.
    else:
        anmfile.seek(24, 1) # Bounding boxes. In order: X1 (X min), X2 (X max), Y1 (Y min), Y2 (Y max). Three short values for each (so X1 0, X1 1, X1 2, and so on).
    PieceCount = struct.unpack('<H', anmfile.read(2))[0] # a.k.a "Cuts". How many pieces the sprites are made up of.
    for s in range(PieceCount):
        PivotX[s] = struct.unpack('<h', anmfile.read(2))[0] # Signed value for the X position offsets of each piece are stored all in a row...
    for s in range(PieceCount):
        PivotY[s] = struct.unpack('<h', anmfile.read(2))[0] # ...and *then* all of the Y position offsets in a row. So "XXXXYYYY", not "XYXYXYXY" in other words.
    for s in range(PieceCount):
        PieceFlags = struct.unpack('<H', anmfile.read(2))[0] # Two bytes shared between two different information sets below.
        if ANMFormat == 1:
            TileStart[s] = PieceFlags & 0x00FF # Bits 1-8 count up to 256 tile IDs.
            PieceSize[s] = (PieceFlags & 0x1F00) << 2 # Bits 9-12 determine chunk sizes. Bit-shift forward so we don't have to make a second set of checks. TODO: Are bits 13-16 used in The Scorpion King?
        elif ANMFormat == 2:
            TileStart[s] = PieceFlags & 0x007F # Bits 1-7 count up to 128 tile IDs.
            PieceSize[s] = (PieceFlags & 0x0F80) << 3 # Bits 8-11 determine chunk sizes. Bit-shift forward so we don't have to make a second set of checks. TODO: Are bits 12-16 used in Rescue Heroes?
        else:
            TileStart[s] = PieceFlags & 0x03FF # Bits 1-10 count up to 1024 tile IDs.
            PieceSize[s] = (PieceFlags & 0xFC00) # Bits 11-14 determine chunk sizes, bit 15 = uses second palette, bit 16 = 256-colour.
        if PieceSize[s] & 0x3C00 == 0x0000:
            TileWidth[s] = 1; TileHeight[s] = 1 # 1x1 tile chunk for a 8x8 sprite.
        elif PieceSize[s] & 0x3C00 == 0x0400:
            TileWidth[s] = 2; TileHeight[s] = 1 # 2x1 tile chunk for a 16x8 sprite.
        elif PieceSize[s] & 0x3C00 == 0x0800:
            TileWidth[s] = 1; TileHeight[s] = 2 # 1x2 tile chunk for a 8x16 sprite.
        elif PieceSize[s] & 0x3C00 == 0x1000:
            TileWidth[s] = 2; TileHeight[s] = 2 # 2x2 tile chunk for a 16x16 sprite.
        elif PieceSize[s] & 0x3C00 == 0x1400:
            TileWidth[s] = 4; TileHeight[s] = 1 # 4x1 tile chunk for a 32x8 sprite.
        elif PieceSize[s] & 0x3C00 == 0x1800:
            TileWidth[s] = 1; TileHeight[s] = 4 # 1x4 tile chunk for a 8x32 sprite.
        elif PieceSize[s] & 0x3C00 == 0x2000:
            TileWidth[s] = 4; TileHeight[s] = 4 # 4x4 tile chunk for a 32x32 sprite (most common).
        elif PieceSize[s] & 0x3C00 == 0x2400:
            TileWidth[s] = 4; TileHeight[s] = 2 # 4x2 tile chunk for a 32x16 sprite.
        elif PieceSize[s] & 0x3C00 == 0x2800:
            TileWidth[s] = 2; TileHeight[s] = 4 # 2x4 tile chunk for a 16x32 sprite.
        elif PieceSize[s] & 0x3C00 == 0x3000:
            TileWidth[s] = 8; TileHeight[s] = 8 # 8x8 tile chunk for a 64x64 sprite.
        elif PieceSize[s] & 0x3C00 == 0x3400:
            TileWidth[s] = 8; TileHeight[s] = 4 # 8x4 tile chunk for a 64x32 sprite.
        elif PieceSize[s] & 0x3C00 == 0x3800:
            TileWidth[s] = 4; TileHeight[s] = 8 # 4x8 tile chunk for a 32x64 sprite.
        else:
            print("Unknown piece size at " + str(hex(anmfile.tell())) + " (" + str(hex(PieceSize[s])) + ")!")

    if TileBounds == True:
        result_image = Image.new('RGBA', (SpriteWidth, SpriteHeight), (0, 0, 0, 0)) # Initializing the assembled (transparent) sprite PNG in memory.
    else:
        result_image = Image.new('P', (SpriteWidth, SpriteHeight), (0, 0, 0, 255)) # Initializing the assembled (palettized) sprite PNG in memory.
    for s in range(PieceCount):
        anmfile.seek(FrameStart[x] + (TileStart[s] * 32), 0) # Jump to the beginning of the piece's tiles.
        # print(str(PivotX[s]) + "," + str(PivotY[s]) + " | " + str(hex(PieceSize[s])) + " | " + str(TileStart[s])) # Uncomment to watch the script print piece information as it builds the sprites.
        TilePasteX = 0; TilePasteY = 0 # Initializing values for chunk assembly.
        TileImage = Image.new('P', (TileWidth[s] * 8, TileHeight[s] * 8), (0, 0, 0, 255)) # Initializing the assembled tile chunk in memory.
        for t in range(TileWidth[s] * TileHeight[s]):
            if PieceSize[s] & 0x8000 == 0x8000 or FrameFlags == 0x8000:
                CropImage = Image.frombuffer('L', (8,8), anmfile.read(0x40), 'raw', 'L', 0, 1)
            else:
                TempTile = bytearray()
                for y in range(32):
                    TileByte = struct.unpack('<B', anmfile.read(1))[0]
                    if PieceSize[s] & 0x4000 == 0x4000:
                        TileByteA = (TileByte & 0x0F) + ((PaletteNum + 1)* 16)
                        if TileByteA & 0x0F == 0:
                            TileByteA = 0 # Use index 0 for a global transparency instead of that line's specific transparency value.
                        TileByteB = ((TileByte & 0xF0) >> 4) + ((PaletteNum + 1) * 16)
                        if TileByteB & 0x0F == 0:
                            TileByteB = 0 # Use index 0 for a global transparency instead of that line's specific transparency value.
                    else:
                        TileByteA = (TileByte & 0x0F) + (PaletteNum * 16)
                        if TileByteA & 0x0F == 0:
                            TileByteA = 0 # Use index 0 for a global transparency instead of that line's specific transparency value.
                        TileByteB = ((TileByte & 0xF0) >> 4) + (PaletteNum * 16)
                        if TileByteB & 0x0F == 0:
                            TileByteB = 0 # Use index 0 for a global transparency instead of that line's specific transparency value.
                    TempTile.append(TileByteA)
                    TempTile.append(TileByteB)
                CropImage = Image.frombuffer('L', (8,8), TempTile, 'raw', 'L', 0, 1)
            if TileBounds == True:
                TileImage.putpalette(ANMPalette) # If using the "TileBounds" option, apply the palette before pasting it instead of after.
            TileImage.paste(CropImage, (TilePasteX * 8, TilePasteY * 8), mask=0) # Pasting the tile in the right spot.
            TilePasteX = TilePasteX + 1 # Shift right by 1 tile.
            if TilePasteX == TileWidth[s]:
                TilePasteX = 0 # We've reached the edge, so we reset and...
                TilePasteY = TilePasteY + 1 # ...move onto the next line.
        result_image.paste(TileImage, (PivotX[s] + (SpriteWidth // 2), PivotY[s] + (SpriteHeight // 2)), mask=0) # Paste the assembled tile into the sprite PNG.

    if UseGBAROM == True:
        outfile = (str(SpriteStart) + '/' + str(x) + '.png') # Setting up the file path.
    else:
        outfile = (SpriteName + '/' + str(x) + '.png') # Setting up the file path.
    if TileBounds == False:
        result_image.putpalette(ANMPalette) # Applying the palette to the resulting image.
    result_image.save(outfile) # Saving the file.
    print("Saved to " + outfile) # We did the thing.

if UseGBAROM == True:
    print("The next file should (theoretically) start at around " + str(hex(SpriteTileStart + SpriteTileSize)) + " in " + ROMName + ".")
    os.system('pause')