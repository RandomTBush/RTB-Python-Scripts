import os
import sys
import platform
import glob
import struct
from PIL import Image, ImagePalette

# WayForward GBA/DS/LeapFrog Didj/Leapster tileset (*.TS4 / *.TS8) metatile extraction script written by Random Talking Bush.
# Based only slightly on onepill's TextureUnpacker script: https://github.com/onepill/texture_unpacker_scirpt

TSFormat = 0 # See the list below for which value should be used for the game you're ripping from.
TilesetName = "365" # The name of the tileset TS4/TS8 file, minus extension. Will also be the exported image's filename with a "_metatile" suffix added. (Example: "363" and "365" are for the Bramble Maze's background and foreground .TS4 filenames respectively when using my QuickBMS script to unpack Shantae Advance: Risky Revolution.)
SceneName = "362" # The name of the .SCN or .PAL file to use the palette from, minus extension. Leave blank to use a grayscale palette. (Example: "362" is filename for the Bramble Maze scene when using my QuickBMS script to unpack Shantae Advance: Risky Revolution.) Ignored when TSFormat = 4 (Leapster sprites have no separate palettes).

UseGBAROM = False # Change this to True to read from a GBA ROM instead of a .TS4/.TS8 file. Make sure both the "ROMName" and "TilesetStart" lines below are filled in correctly. For experts only -- you're better off using my QuickBMS scripts to unpack the ROM files instead.
ROMName = "Shantae.gba" # Game Boy Advance ROM file needed to extract tile data. Ignored when UseGBAROM is False (it uses the "TilesetName" above instead).
TilesetStart = 0x962774 # Offset to the start of metatile data in a GBA ROM. Ignored when UseGBAROM is False. (Example: 0x962774 is the offset to the Bramble Maze's foreground .TS4 in Shantae Advance: Risky Revolution.)
SceneStart = 0x95C5DC # Offset to the start of scene data in a GBA ROM. Ignored when UseGBAROM is False. (Example: 0x95C5DC is the offset to the Bramble Maze's SCN file in Shantae Advance: Risky Revolution.)
TileDelimiter = False # Debug option for GBA tilesets with more than 1024 tiles (see "BROKEN TILESETS" section below). This will start ignoring the tile flip flags as soon as it detects a tile with ID 0x0400 (which would correspond to a horizontally-flipped blank tile). This will not "repair" the tileset, but it will make the last section at least *somewhat* legible.
RawPalette = True # Set this to True to read palette values as multiples of 8 (0, 8, 16, etc. with max of 248 for DS or 240 for Leapster). Set this to False to recalculate them to 255 maximum like most emulators would display.

# Instructions on how to use this script:
# 1. Install both Python (either 2 or 3, both work) and Pillow: https://github.com/python-pillow/Pillow
# 2. If ripping from a GBA game, use QuickBMS (https://aluigi.altervista.org/quickbms.htm) and one of my "WayForwardGBA" scripts (https://github.com/RandomTBush/RTB-QuickBMS-Scripts/tree/master/Archive) to unpack the game you want to rip from. For DS or Didj games, you can use something like Tinke to unpack the former and 7-Zip for the latter.
# 3. For a .TS4/.TS8 file, set the UseGBAROM option to False. Change the path for the "TilesetName" entry above to the name of the .TS4/.TS8 file you want to extract from , and set "SceneName" to the SCN file you want to user the palette from.
# 4. Run the script (no additional command-line parameters needed). If everything's ret-2-go, then resulting "metatile" set can be found in the same folder as the script. This can be used with my "LYR" script to generate a complete screen / map image.

# ROM-file ripping (for experts):
# 3B. Set the UseGBAROM option to True, change the name for the "ROMName" entry to match the GBA ROM you want to try extracting a tileset from (eg. "Shantae.gba", it can either be a relative name or a full path), and the "TilesetName" entry to the name of the extracted tileset PNG (see #4 in the previous section).
# 3C. Locate the start of the tileset information in the GBA ROM, which has the visual appearance of random pixels scattered about and is always located above the tileset (not below). At the very top of the "thinner" set and immediately following the tiles of the previous sprite set should be the offset you want to fill in for the "SpriteStart" value above.

# Troubleshooting:
# If the script throws an error or doesn't export anything, check to make sure that you have the right "TSFormat" and "TilesetName" values filled in.
# If extracting from a GBA ROM instead of a .TS4/.TS8 file, make sure that the "TilesetStart" offset ends in either 0, 4, 8 or C, double-check in a hex editor to make sure you're in the right spot if you need to. The metatile assembly data starts with either 0x0000, 0x0001, or 0x0010 usually, with a block of eight "00" bytes a few ahead of it (the first metatile is always empty). Shift it forward or backward by 4 at a time if you need to.

# Works with the following games:
# --------------------------------------------------------------------------------
# Game Boy Advance:
# American Dragon: Jake Long - Rise of the Huntsclan        [Set TSFormat = 1]
# Barbie and the Magic of Pegasus                           [Set TSFormat = 1]
# Barbie in the 12 Dancing Princesses                       [Set TSFormat = 1]
# Barbie: The Princess and the Pauper                       [Set TSFormat = 0]
# Godzilla: Domination                                      [Set TSFormat = 0]
# Justice League Heroes: The Flash                          [Set TSFormat = 1]
# Looney Tunes: Double Pack - Dizzy Driving / Acme Antics   [Set TSFormat = 1]
# Rescue Heroes: Billy Blazes                               [Set TSFormat = 0]
# The Scorpion King: Sword of Osiris                        [Set TSFormat = 0]
# Sigma Star Saga                                           [Set TSFormat = 1]
# Shantae Advance: Risky Revolution                         [Set TSFormat = 1]
# Shantae Advance: Risky Revolution (Battle Mode)           [Set TSFormat = 0]
# Shantae Advance: Risky Revolution (Demo)                  [Set TSFormat = 0]
# SpongeBob SquarePants: Creature from the Krusty Krab      [Set TSFormat = 1]
# SpongeBob SquarePants: Lights, Camera, Pants!             [Set TSFormat = 1]
# The SpongeBob SquarePants Movie                           [Set TSFormat = 0]
# Tak: The Great Juju Challenge                             [Set TSFormat = 1]
# Unfabulous!                                               [Set TSFormat = 1]
# X-Men: The Official Game                                  [Set TSFormat = 1]
# --------------------------------------------------------------------------------
# DS/DSi:
# Aliens: Infestation                                       [Set TSFormat = 2]
# American Dragon: Jake Long - Attack of the Dark Dragon    [Set TSFormat = 1]
# Barbie and the Three Musketeers                           [Set TSFormat = 2]
# Barbie in the 12 Dancing Princesses                       [Set TSFormat = 1]
# Batman: The Brave and the Bold                            [Set TSFormat = 2]
# Contra 4                                                  [Set TSFormat = 2]
# Despicable Me: Minion Mayhem                              [Set TSFormat = 2]
# Galactic Taz Ball                                         [Set TSFormat = 2]
# Looney Tunes: Duck Amuck                                  [Set TSFormat = 1]
# Mighty Flip Champs                                        [Set TSFormat = 2]
# Mighty Milky Way                                          [Set TSFormat = 2]
# Shantae: Risky's Revenge                                  [Set TSFormat = 2]
# Shrek: Ogres & Dronkeys                                   [Set TSFormat = 2]
# Space Chimps                                              [Set TSFormat = 2]
# SpongeBob SquarePants: Creature from the Krusty Krab      [Set TSFormat = 1]
# Thor: God of Thunder                                      [Set TSFormat = 2]
# Where the Wild Things Are                                 [Set TSFormat = 2]
# --------------------------------------------------------------------------------
# LeapFrog Didj [Both games use TSFormat = 3]:
# Nicktoons: Android Invasion
# SpongeBob SquarePants: Fists of Foam
# --------------------------------------------------------------------------------
# LeapFrog Leapster [All games use TSFormat = 4]:
# Cosmic Math
# Letterpillar
# Number Raiders
# The Batman: Multiply, Divide and Conquer
# The Batman: Strength in Numbers
# Word Chasers
# --------------------------------------------------------------------------------
# LeapFrog Leapster Explorer [Use TSFormat = 3]:
# SpongeBob SquarePants: Fists of Foam
# --------------------------------------------------------------------------------
# BROKEN TILESETS:
# Justice League Heroes: The Flash = 371
# Looney Tunes: Double Pack - Dizzy Driving / Acme Antics = 190 and 192
# Shantae Advance: Risky Revolution = 349, 652 and 731
# SpongeBob SquarePants: Creature from the Krusty Krab = 402 and 520
# Tak: The Great Juju Challenge: = 311
# Unfabulous! = 191 and 236
# --------------------------------------------------------------------------------
# Everything below this line should be left alone.

if UseGBAROM == False:
    TilesetStart = 0x0 # Zeroing out the offset, as .TS4/.TS8 files have it at the beginning.
    if not os.path.exists(TilesetName + ".ts4"):
        if not os.path.exists(TilesetName + ".ts8"):
            print("Can't find '" + TilesetName + ".ts4' or '" + TilesetName + ".ts8'. Check to make sure you filled in the 'TilesetName' entry correctly.")
            os.system('pause')
            exit()
        else:
            ts4file = open(TilesetName + '.ts8', "rb") # Opens a .TS8 file, uses the name listed in "TilesetName" above.
    else:
        ts4file = open(TilesetName + '.ts4', "rb") # Opens a .TS4 file, uses the name listed in "TilesetName" above.
else:
    if not os.path.exists(ROMName):
        print("Can't find " + ROMName + ". Check to make sure you filled in the 'ROMName' entry correctly.")
        os.system('pause')
        exit()
    else:
        ts4file = open(ROMName, "rb") # Opens a ROM file needed to extract tileset data, see the above note for the "TilesetStart" offset.

if TSFormat != 4:
    if UseGBAROM == False and TSFormat == 3:
        # LeapFrog Didj has a 0x200 palette block at the beginning of its .TS4/.TS8 files, which is considered part of the file for its offset calculations.
        print("Didj format tileset, using internal palette.")
        ts4file.seek(0, 0) # Start reading the TS4/TS8 file.
        TS4Palette = bytearray()
        # I am doing it this way for the sake of "raw" palettes, and so that the method is compatible with both Python 2 and 3.
        for x in range(256):
            PaletteBytes = struct.unpack('<H', ts4file.read(2))[0]
            PaletteByteA = ((PaletteBytes & 0x001F)) * 8
            PaletteByteB = ((PaletteBytes & 0x03E0) >> 5) * 8
            PaletteByteC = ((PaletteBytes & 0x7C00) >> 10) * 8
            if RawPalette == False:
                PaletteByteA = PaletteByteA + ((PaletteByteA + 1) // 32)
                PaletteByteB = PaletteByteB + ((PaletteByteB + 1) // 32)
                PaletteByteC = PaletteByteC + ((PaletteByteC + 1) // 32)
            TS4Palette.append(PaletteByteA)
            TS4Palette.append(PaletteByteB)
            TS4Palette.append(PaletteByteC)
    else:
        ts4file.seek(TilesetStart, 0) # Start reading the .TS4 / .TS8 / ROM file.
        if os.path.exists(SceneName + ".pal") or os.path.exists(SceneName + ".scn"):
            if os.path.exists(SceneName + ".pal"):
                scnfile = open(SceneName + ".pal", "rb") # Opens a .PAL file to extract palette information from.
            elif os.path.exists(SceneName + ".scn"):
                scnfile = open(SceneName + ".scn", "rb") # Opens a .SCN file to extract palette information from.
            scnfile.seek(0, 0) # Background palettes are in the first half of the SCN file.
            TS4Palette = bytearray()
            # I am doing it this way for the sake of "raw" palettes, and so that the method is compatible with both Python 2 and 3.
            for x in range(256):
                PaletteBytes = struct.unpack('<H', scnfile.read(2))[0]
                PaletteByteA = ((PaletteBytes & 0x001F)) * 8
                PaletteByteB = ((PaletteBytes & 0x03E0) >> 5) * 8
                PaletteByteC = ((PaletteBytes & 0x7C00) >> 10) * 8
                if RawPalette == False:
                    PaletteByteA = PaletteByteA + ((PaletteByteA + 1) // 32)
                    PaletteByteB = PaletteByteB + ((PaletteByteB + 1) // 32)
                    PaletteByteC = PaletteByteC + ((PaletteByteC + 1) // 32)
                TS4Palette.append(PaletteByteA)
                TS4Palette.append(PaletteByteB)
                TS4Palette.append(PaletteByteC)
        else:
            if SceneName == "":
                print("Defaulting to grayscale palette.")
            else:
                print("Couldn't find '" + SceneName + ".scn' or '" + SceneName + ".pal', defaulting to grayscale instead.")
            TS4Palette = bytearray() # Forcing a grayscale palette for Python 3 compatibility.
            for x in range(256):
                TS4Palette.append(x) 
                TS4Palette.append(x)
                TS4Palette.append(x)

TilesetFlags = struct.unpack('<H', ts4file.read(2))[0] # Flags. 0x0001 = 256-colour / .TS8 file, 0x0004 = LZSS-compressed, 0x0010 = ???.
MetatileCount = struct.unpack('<H', ts4file.read(2))[0] # How many 16x16 metatiles (consisting of four 8x8 tiles) there are.
TileCount = struct.unpack('<H', ts4file.read(2))[0] # How many 8x8 tiles there are.
if TSFormat > 0:
    MetatileUnk = struct.unpack('<H', ts4file.read(2))[0] # Early GBA games don't have a fourth set of bytes in the header.

if TSFormat == 2 or TSFormat == 3:
    TileOffset = (ts4file.tell() + (MetatileCount * 16)) # DS/Didj games have twice the buffer size compared to the GBA games.
elif TSFormat == 4:
    TileFlipRet = (ts4file.tell() + (MetatileCount * 8)) # Leapster games have an additional buffer meant for tile flip flags, after the metatile data and before the tile graphics. Store it for later.
    TileOffset = TileFlipRet + (MetatileCount * 4) # Add the tile flip buffer to the offset as well.
else:
    TileOffset = (ts4file.tell() + (MetatileCount * 8))

if TileCount > 1024 and TSFormat < 2:
    print("WARNING: Tileset uses GBA format and has over 1024 tiles. Expect broken metatiles.")

SheetHeight = (MetatileCount & 0xFFF0) # Maths to determine how large the metatile sheet needs to be
if (MetatileCount & 0x000F) != 0:
    SheetHeight = SheetHeight + 16 # If it's not a full line, compensate for leftovers.

MetatilePasteX = 0; MetatilePasteY = 0 # Initializing values for metatile assembly.
if TSFormat == 4:
    TileImage = Image.new('RGBA', (256, SheetHeight), (0, 0, 0, 0)) # Initializing a full-colour metatile PNG in memory.
else:
    TileImage = Image.new('P', (256, SheetHeight), (0, 0, 0, 255)) # Initializing a paletted metatile PNG in memory.
TileFix = False # In case of emergency, break glass.

for x in range(MetatileCount):
    for y in range(4):
        if TSFormat == 2 or TSFormat == 3:
            MetatileFlags = struct.unpack('<L', ts4file.read(4))[0] # Four bytes shared between three different information sets below.
            TileID = (MetatileFlags & 0x0000FFFF) # I don't know the upper limit for this (one of the largest TS4 files, FV_PF_ALL_TS4_NIGHT.ts4 from Where the Wild Things Are, goes up to 0x0875 / 2165).
            TileFlip = (MetatileFlags & 0x0C000000) >> 26 # Second nibble controls horizontal flip (4), vertical flip (8) or both (C).
            TilePalette = (MetatileFlags & 0xF0000000) >> 24 # Upper nibble controls which palette set it uses.
        elif TSFormat == 4:
            TileID = struct.unpack('<H', ts4file.read(2))[0] # No "flags" so to speak, simply a two-byte tile ID.
            TileRet = ts4file.tell() # We'll be back in a sec.
            ts4file.seek(TileFlipRet, 0) # Hop to the tile flip buffer from earlier.
            TileFlip = (struct.unpack('<B', ts4file.read(1))[0]) >> 2 # Only values are 0x00 (none), 0x04 (horizontal flip), 0x08 (vertical flip, and 0x0C (both).
            TileFlipRet = TileFlipRet + 1 # Add one to the offset.
            ts4file.seek(TileRet, 0) # And back to where we were earlier.
        else:
            MetatileFlags = struct.unpack('<H', ts4file.read(2))[0] # Two bytes shared between three different information sets below.
            if TileDelimiter == True and MetatileFlags & 0x0FFF == 0x0400:
                TileFix = True # Flip the switch.
            if TileFix == True:
                TileID = (MetatileFlags & 0x07FF) # Time to break things. Or "un-break" things. Either way.
                TileFlip = 0 # Ignoring the horizontal and vertical flip flags since the former's been absorbed by tile #1024+.
            else:
                TileID = (MetatileFlags & 0x03FF) # Up to 1024 tiles, including a blank one.
                TileFlip = (MetatileFlags & 0x0C00) >> 10 # Second nibble controls horizontal flip (4), vertical flip (8) or both (C).
            TilePalette = (MetatileFlags & 0xF000) >> 8 # Upper nibble controls which palette set it uses.
        if TileID != 0xCCCC:
            if TSFormat != 4:
                TileRet = ts4file.tell() # We'll be back in a sec.
            # Didj tilesets have 0xCCCC as an "end of file" identifier.
            if TilesetFlags & 0x0001 == 1:
                if TSFormat != 4:
                    ts4file.seek(TileOffset + (TileID * 0x40), 0)
                    CropImage = Image.frombuffer('L', (8,8), ts4file.read(0x40), 'raw', 'L', 0, 1)
                else:
                    ts4file.seek(TileOffset + (TileID * 0x80), 0)
                    TempTile = bytearray()
                    for x in range(64):
                        TileBytes = struct.unpack('<H', ts4file.read(2))[0] # Leapster uses ARGB4444, two bytes per pixel.
                        if RawPalette == True:
                            TileByteA = ((TileBytes & 0x0F00) >> 8) * 16 # Second "nibble" is the red value.
                            TileByteB = ((TileBytes & 0x00F0) >> 4) * 16 # Third "nibble" is the green value.
                            TileByteC = (TileBytes & 0x000F) * 16 # Fourth "nibble" is the blue value.
                        else:
                            TileByteA = ((TileBytes & 0x0F00) >> 8) + (((TileBytes & 0x0F00) >> 8) * 16) # Second "nibble" is the red value.
                            TileByteB = ((TileBytes & 0x00F0) >> 4) + (((TileBytes & 0x00F0) >> 4) * 16) # Third "nibble" is the green value.
                            TileByteC = (TileBytes & 0x000F) + ((TileBytes & 0x000F) * 16) # Fourth "nibble" is the blue value.
                        TileByteD = ((((TileBytes & 0xF000) >> 12) + (((TileBytes & 0xF000) >> 12) * 16)) * -1) + 255 # First "nibble" is the alpha value. The alpha value is inverted, so we need to fix that.
                        TempTile.append(TileByteA)
                        TempTile.append(TileByteB)
                        TempTile.append(TileByteC)
                        TempTile.append(TileByteD)
                    CropImage = Image.frombuffer('RGBA', (8,8), TempTile, 'raw', 'RGBA', 0, 1)
            else:
                ts4file.seek(TileOffset + (TileID * 0x20), 0)
                TempTile = bytearray()
                for x in range(32):
                    TileByte = struct.unpack('<B', ts4file.read(1))[0]
                    TileByteA = (TileByte & 0x0F) + TilePalette
                    if TileByteA & 0x0F == 0:
                        TileByteA = 0 # Use index 0 for a global transparency instead of that line's specific transparency value.
                    TileByteB = ((TileByte & 0xF0) >> 4) + TilePalette
                    if TileByteB & 0x0F == 0:
                        TileByteB = 0 # Use index 0 for a global transparency instead of that line's specific transparency value.
                    TempTile.append(TileByteA)
                    TempTile.append(TileByteB)
                CropImage = Image.frombuffer('L', (8,8), TempTile, 'raw', 'L', 0, 1)
            if TileFlip == 1:
                CropImage = CropImage.transpose(Image.FLIP_LEFT_RIGHT) # A nibble of "4" means the tile is flipped horizontally.
            elif TileFlip == 2:
                CropImage = CropImage.transpose(Image.FLIP_TOP_BOTTOM) # A nibble of "8" means the tile is flipped vertically.
            elif TileFlip == 3:
                CropImage = CropImage.transpose(Image.FLIP_LEFT_RIGHT) # A nibble of "C" means the tile is flipped both horizontally...
                CropImage = CropImage.transpose(Image.FLIP_TOP_BOTTOM) # ...and vertically.
            if y == 0:
                TileImage.paste(CropImage, ((MetatilePasteX * 16), (MetatilePasteY * 16)), mask=0) # Pasting the upper-left quadrant.
            elif y == 1:
                TileImage.paste(CropImage, ((MetatilePasteX * 16) + 8, (MetatilePasteY * 16)), mask=0) # Pasting the upper-right quadrant.
            elif y == 2:
                TileImage.paste(CropImage, ((MetatilePasteX * 16), (MetatilePasteY * 16) + 8), mask=0) # Pasting the lower-left quadrant.
            elif y == 3:
                TileImage.paste(CropImage, ((MetatilePasteX * 16) + 8, (MetatilePasteY * 16) + 8), mask=0) # Pasting the lower-right quadrant.
            ts4file.seek(TileRet, 0)
    MetatilePasteX = MetatilePasteX + 1 # Shift right by 1 metatile.
    if MetatilePasteX == 16:
        MetatilePasteX = 0 # We've reached the edge, so we reset and...
        MetatilePasteY = MetatilePasteY + 1 # ...move onto the next line.

outfile = (TilesetName + '_metatile.png') # Setting up the file path.
if TSFormat != 4:
    TileImage.putpalette(TS4Palette) # Load the palette (but only if it's not a Leapster TS8).
TileImage.save(outfile) # Saving the file.
print("Saved to " + outfile) # We did the thing.

if UseGBAROM == True:
    if TilesetFlags & 0x0001 == 1:
        print("The next file should (theoretically) start at around " + str(hex(ts4file.tell() + (TileCount * 64))) + " in " + ROMName + ".")
    else:
        print("The next file should (theoretically) start at around " + str(hex(ts4file.tell() + (TileCount * 32))) + " in " + ROMName + ".")
    os.system('pause')