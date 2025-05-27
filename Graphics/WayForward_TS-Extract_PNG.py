import os
import sys
import platform
import glob
import struct
from PIL import Image

# WayForward GBA/DS/LeapFrog Didj tileset (*.TS4 / *.TS8) metatile extraction script written by Random Talking Bush.
# Based only slightly on onepill's TextureUnpacker script: https://github.com/onepill/texture_unpacker_scirpt

TSFormat = 0 # See the list below for which value should be used for the game you're ripping from.
TilesetName = "365" # The name of the tileset PNG file(s). (Example: "365" will be the Bramble Maze's foreground .TS4 filename when using my QuickBMS script to unpack Shantae Advance: Risky Revolution.)

UseGBAROM = False # Change this to True to read from a GBA ROM instead of a .TS4/.TS8 file. Make sure both the "ROMName" and "TilesetStart" lines below are filled in correctly. For experts only -- you're better off using my QuickBMS scripts to unpack the ROM files instead.
ROMName = "Shantae.gba" # Game Boy Advance ROM file needed to extract tile data. Ignored when UseGBAROM is False (it uses the "TilesetName" above instead).
TilesetStart = 0x962774 # Offset to the start of metatile data in a GBA ROM. Ignored when UseGBAROM is False. (Example: 0x962774 is the offset to the Bramble Maze's foreground .TS4 in Shantae Advance: Risky Revolution.)
TileDelimiter = False # Debug option for GBA tilesets with more than 1024 tiles (see "BROKEN TILESETS" section below). This will start ignoring the tile flip flags as soon as it detects a tile with ID 0x0400 (which would correspond to a horizontally-flipped blank tile). This will not "repair" the tileset, but it will make the last section at least *somewhat* legible.

# Instructions on how to use this script:
# 1. Install both Python (either 2 or 3, both work) and Pillow: https://github.com/python-pillow/Pillow
# 2. If ripping from a GBA game, use QuickBMS (https://aluigi.altervista.org/quickbms.htm) and one of my "WayForwardGBA" scripts (https://github.com/RandomTBush/RTB-QuickBMS-Scripts/tree/master/Archive) to unpack the game you want to rip from. For DS or Didj games, you can use something like Tinke to unpack the former and 7-Zip for the latter.
# 3. For a .TS4/.TS8 file, set the UseGBAROM option to False. Change the path for the "TilesetName" entry above to the name of the .TS4/.TS8 file you want to extract (if UseGBAROM = False, otherwise see the section below).
# 4. Extract the tileset graphics for the respective .TS4/.TS8 file (or GBA ROM) using a tile-viewing program such as TiledGGD (https://www.romhacking.net/utilities/646/). Using one of my QuickBMS scripts to split a GBA ROM's filesystem will make additional files with a "_tiles.bin" suffix, which will make that step easier to set up. Pair those tiles up with their respective palettes from either the first half of a .SCN file or a savestate, and make sure that the extracted tileset matches the .TS4/.TS8 file's name (a set of 16 PNGs for .TS4 files, e.g. "scuttletown_pf.ts4" -> "scuttletown_pf_0.png" through "scuttletown_pf_15.png", or just a single PNG for .TS8 files, e.g. "logo_wayforward.ts8" -> "logo_wayforward.png"), is 128 pixels in width and has a height that encompasses the entire sprite tileset. The "BrambleMaze_#.png" and "scuttletown_pf_#.png" samples supplied from Shantae Advance and Risky's Revenge respectively will give you an example of what you're aiming for regarding .TS4 files.
# 4B. While .TS8 files only need a single PNG file, .TS4 files will need an additional step. For those, you need to extract 16 copies of the tileset suffixed with _0, _1, _2, and so on until _15, one with each of the 16 background palettes applied to it in order from top to bottom (see above note and sample files if needed).
# 5. Run the script (no additional command-line parameters needed). If everything's ret-2-go, then resulting "metatile" set can be found in the same folder as the script. This can be used with my "LYR" script to generate a complete screen / map image.

# ROM-file ripping (for experts):
# 3B. Set the UseGBAROM option to True, change the name for the "ROMName" entry to match the GBA ROM you want to try extracting a tileset from (eg. "Shantae.gba", it can either be a relative name or a full path), and the "TilesetName" entry to the name of the extracted tileset PNG (see #4 in the previous section).
# 3C. Locate the start of the tileset information in the GBA ROM, which has the visual appearance of random pixels scattered about and is always located above the tileset (not below). At the very top of the "thinner" set and immediately following the tiles of the previous sprite set should be the offset you want to fill in for the "SpriteStart" value above.

# Troubleshooting:
# If the script throws an error or doesn't export anything, check to make sure that you have the right "TSFormat" value filled in. If extracting from a GBA ROM instead of a .TS4/.TS8 file, make sure that the "TilesetStart" offset ends in either 0, 4, 8 or C, double-check in a hex editor to make sure you're in the right spot if you need to. The metatile assembly data starts with either 0x0000, 0x0001, or 0x0010 usually, with a block of eight "00" bytes a few ahead of it (the first metatile is always empty). Shift it forward or backward by 4 at a time if you need to.
# If the assembled tileset seems to be garbled, make sure that your tileset PNG(s) has a width of 128 pixels (I didn't code it to check for different widths, sorry), and that it is correctly aligned to the beginning of the tileset data. If you're using a "_tiles.bin" exported from one of my GBA-splitting QuickBMS scripts, the starting offset won't need to be adjusted, otherwise you might need to shift forward or backward by a tile, and make sure it starts with a blank tile.

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
# LeapFrog Didj:
# Nicktoons: Android Invasion                               [Set TSFormat = 3]
# SpongeBob SquarePants: Fists of Foam                      [Set TSFormat = 3]
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
        ts4file = open(TilesetName + '.ts4', "rb") # Opens a .TS8 file, uses the name listed in "TilesetName" above.
else:
    if not os.path.exists(ROMName):
        print("Can't find " + ROMName + ". Check to make sure you filled in the 'ROMName' entry correctly.")
        os.system('pause')
        exit()
    else:
        ts4file = open(ROMName, "rb") # Opens a ROM file needed to extract tileset data, see the above note for the "TilesetStart" offset.

if UseGBAROM == False and TSFormat == 3:
    ts4file.seek(512, 0) # LeapFrog Didj has a 0x200 palette block at the beginning of its .TS4/.TS8 files, which is considered part of the file for its offset calculations.
else: 
    ts4file.seek(TilesetStart, 0) # Start reading the ROM/TS4/TS8 file.

TilesetFlags = struct.unpack('<H', ts4file.read(2))[0] # Flags. 0x0001 = 256-colour / .TS8 file, 0x0004 = LZSS-compressed, 0x0010 = ???.
MetatileCount = struct.unpack('<H', ts4file.read(2))[0] # How many 16x16 metatiles (consisting of four 8x8 tiles) there are.
TileCount = struct.unpack('<H', ts4file.read(2))[0] # How many 8x8 tiles there are.
if TSFormat > 0:
    MetatileUnk = struct.unpack('<H', ts4file.read(2))[0] # Early GBA games don't have a fourth set of bytes in the header.

if TileCount > 1024 and TSFormat < 2:
    print("WARNING: Tileset uses GBA format and has over 1024 tiles. Expect broken metatiles.")
if TSFormat == 2 or TSFormat == 3:
    TileOffset = (ts4file.tell() + (MetatileCount * 16)) # DS/Didj games have twice the buffer size compared to the GBA games.
else:
    TileOffset = (ts4file.tell() + (MetatileCount * 8))

if TilesetFlags & 0x0001 == 1:
    if not os.path.exists(TilesetName + '.png'):
        if UseGBAROM == False:
            print("Can't find tileset image ('" + TilesetName + ".png'). You should find the tiles at offset " + str(hex(TileOffset)) + " in the '" + TilesetName + "' file.")
        else:
            print("Can't find tileset image ('" + TilesetName + ".png'). You should find the tiles at offset " + str(hex(TileOffset)) + " in the '" + ROMName + "' file (if this doesn't lead to tile data, you likely have the wrong offset for 'TilesetStart').")
        os.system('pause')
        exit()
    else:
        sprfile = Image.open(TilesetName + '.png') # Open up the 256-colour paletted tileset image.
else:
    if not os.path.exists(TilesetName + '_0.png'):
        if UseGBAROM == False:
            print("Can't find tileset images ('" + TilesetName + "_0.png'). You should find the tiles at offset " + str(hex(TileOffset)) + " in the '" + TilesetName + "' file.")
        else:
            print("Can't find tileset images ('" + TilesetName + "_0.png'). You should find the tiles at offset " + str(hex(TileOffset)) + " in the '" + ROMName + "' file (if this doesn't lead to tile data, you likely have the wrong offset in 'TilesetStart').")
        os.system('pause')
        exit()
    else:
        sprfile0 = Image.open(TilesetName + '_0.png') # Open up the first paletted tileset image...
        sprfile1 = Image.open(TilesetName + '_1.png') # ...and the second...
        sprfile2 = Image.open(TilesetName + '_2.png') # ...et cetera... I don't need to comment every single one of these.
        sprfile3 = Image.open(TilesetName + '_3.png')
        sprfile4 = Image.open(TilesetName + '_4.png')
        sprfile5 = Image.open(TilesetName + '_5.png')
        sprfile6 = Image.open(TilesetName + '_6.png')
        sprfile7 = Image.open(TilesetName + '_7.png')
        sprfile8 = Image.open(TilesetName + '_8.png')
        sprfile9 = Image.open(TilesetName + '_9.png')
        sprfileA = Image.open(TilesetName + '_10.png')
        sprfileB = Image.open(TilesetName + '_11.png')
        sprfileC = Image.open(TilesetName + '_12.png')
        sprfileD = Image.open(TilesetName + '_13.png')
        sprfileE = Image.open(TilesetName + '_14.png')
        sprfileF = Image.open(TilesetName + '_15.png') # ...up to the 16th.

SheetHeight = (MetatileCount & 0xFFF0) # Maths to determine how large the metatile sheet needs to be
if (MetatileCount & 0x000F) != 0:
    SheetHeight = SheetHeight + 16 # If it's not a full line, compensate for leftovers.

TileStartX = 0; TileStartY = 0; MetatilePasteX = 0; MetatilePasteY = 0 # Initializing values for metatile assembly.
TileImage = Image.new('RGBA', (256, SheetHeight), (0, 0, 0, 0)) # Initializing the assembled metatile PNG in memory.
TileFix = False # In case of emergency, break glass.
for x in range(MetatileCount):
    for y in range(4):
        if TSFormat == 2 or TSFormat == 3:
            MetatileFlags = struct.unpack('<L', ts4file.read(4))[0] # Four bytes shared between three different information sets below.
            TileID = (MetatileFlags & 0x0000FFFF) # I don't know the upper limit for this (one of the largest TS4 files, FV_PF_ALL_TS4_NIGHT.ts4 from Where the Wild Things Are, goes up to 0x0875 / 2165).
            TileFlip = (MetatileFlags & 0x0C000000) >> 26 # Second nibble controls horizontal flip (4), vertical flip (8) or both (C).
            TilePalette = (MetatileFlags & 0xF0000000) >> 28 # Upper nibble controls which palette set it uses.
            TileStartX = (TileID & 0x000F) * 8 # Maths to determine X position of metatile sheet to cut.
            TileStartY = (((TileID & 0xFFF0) // 16) * 8) # More maths to determine Y position of metatile sheet to cut.
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
            TilePalette = (MetatileFlags & 0xF000) >> 12 # Upper nibble controls which palette set it uses.
            TileStartX = (TileID & 0x000F) * 8 # Maths to determine X position of metatile sheet to cut.
            TileStartY = (((TileID & 0xFFF0) // 16) * 8) # More maths to determine Y position of metatile sheet to cut.
        if TilesetFlags & 0x0001 == 1:
            CropImage = sprfile.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8)) # Grabbing the right tile.
        else:
            if TilePalette == 0:
                CropImage = sprfile0.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8)) # Grabbing the right tile from the first paletted tile sheet.
            elif TilePalette == 1:
                CropImage = sprfile1.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8)) # Or the second.
            elif TilePalette == 2:
                CropImage = sprfile2.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8)) # Or the third. You know the drill.
            elif TilePalette == 3:
                CropImage = sprfile3.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 4:
                CropImage = sprfile4.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 5:
                CropImage = sprfile5.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 6:
                CropImage = sprfile6.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 7:
                CropImage = sprfile7.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 8:
                CropImage = sprfile8.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 9:
                CropImage = sprfile9.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 10:
                CropImage = sprfileA.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 11:
                CropImage = sprfileB.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 12:
                CropImage = sprfileC.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 13:
                CropImage = sprfileD.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 14:
                CropImage = sprfileE.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8))
            elif TilePalette == 15:
                CropImage = sprfileF.crop((TileStartX, TileStartY, TileStartX + 8, TileStartY + 8)) # Or the sixteenth. I'm sure there's a better way to go about this, but sometimes redundancy just works.
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
    MetatilePasteX = MetatilePasteX + 1 # Shift right by 1 metatile.
    if MetatilePasteX == 16:
        MetatilePasteX = 0 # We've reached the edge, so we reset and...
        MetatilePasteY = MetatilePasteY + 1 # ...move onto the next line.

outfile = (TilesetName + '_metatile.png') # Setting up the file path.
TileImage.save(outfile) # Saving the file.
print("Saved to " + outfile) # We did the thing.

if UseGBAROM == True:
    if TilesetFlags & 0x0001 == 1:
        print("The next file should (theoretically) start at around " + str(hex(ts4file.tell() + (TileCount * 64))) + " in " + ROMName + ".")
    else:
        print("The next file should (theoretically) start at around " + str(hex(ts4file.tell() + (TileCount * 32))) + " in " + ROMName + ".")
    os.system('pause')