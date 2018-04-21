#py36

import struct
import collections
import zlib
import os
from math import floor

import PIL.Image

import esmlib


# [11:40 PM] Phoenix: This is the stage of the project where I am close enough to accomplishing what I want that I stop implementing QoL improvements and just focus on being done with my original goal
# [11:41 PM] Foreground: That's a bad idea and you know it.
# [11:41 PM] Phoenix: Oh please, when will I ever need this code again?
# *6 months later*
# **FUCK**
# [11:42 PM] Foreground: Can you add a note in comments containing my I-told-you-so?


esm = esmlib.openESM('Oblivion.esm')
esm.interestingTopGroups = [b'WRLD']
esm.load()

print('extracting data')

heightmap = PIL.Image.new("I", (4096,4096), 65536)

tamrielGroup = esm.groups[0].contents[1]

def flipRange(i):
    #converts per-cell coordinates to PIL coordinates
    return (i*-1)+32

def cellCoordToPILCoord(x,y):
    #takes cell coords and returns the PIL coords of the top left pixel
    #y is -60 to +60
    y *= -1 #TES Y axis is backwards
    
    y += 60
    x += 64
    
    y *= 32
    x *= 32
    return x, y

#http://stackoverflow.com/a/434328/432690
def chunker(seq, size=33):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

# debugTmp = True

coords = []
cell = None
for block in tamrielGroup.subgroups:
    for subblock in block:
        for i, entry in enumerate(subblock.contents):
            if entry.type == b"CELL":
                #                           group after cell V                     V temp children in groupType 9
                for record in [x for x in subblock.contents[i+1].contents if x.groupType == 9][0]:
                    if record.type == b'LAND':
                        for subrecord in record.subrecords:
                            if subrecord.type == b'VHGT':
                                
                                coords = None
                                for cellSubrecord in entry.subrecords:
                                    if cellSubrecord.type == b'XCLC':
                                        coords = struct.unpack('ll', cellSubrecord.data)
                                assert coords is not None
                                # print("processing cell " + repr(coords))

                                image = PIL.Image.new("I", (33,33), 65536)

                                offset = struct.unpack('f', subrecord.data[:4])[0]
                                firstValueOfRow = None
                                for j, row in enumerate(chunker(subrecord.data[4:1093])):
                                    previousPixel = None
                                    datas = struct.unpack('33b', row)
                                    for k, data in enumerate(datas):
                                        # print(repr(previousPixel))
                                        # import code
                                        # code.interact(local=locals())
                                        if k == 0:
                                            tmp = firstValueOfRow if firstValueOfRow else 0
                                            pixel = data + tmp
                                            firstValueOfRow = pixel
                                        else:
                                            pixel = data + previousPixel
                                        previousPixel = pixel
                                        pixel += offset
                                        # print(str(pixel))
                                        image.putpixel((k,flipRange(j)), floor(pixel))


                                #compute PIL coordinates and paste image there
                                coords = cellCoordToPILCoord(*coords)

                                heightmap.paste(image, coords)
                                
                                # if debugTmp:
                                #     import code
                                #     code.interact(local=locals())
                                
                continue




print('saving heightmap')
heightmap.save('heightmap.png')