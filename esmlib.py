#py36

import struct
import collections
import zlib
import io
from math import floor

import inspect #for debugging caller lookups. do we need this?

'''
Reading CELL 6.3 seconds
Reading WRLD 19.6 seconds
Reading literally everything else 1.3 seconds
'''

class ESM(object):
    """An ESM file. You should probably get these with esmlib.open() though"""
    def __init__(self, file):
        super(ESM, self).__init__()
        self.file = file
        self.top = None
        self.groups = []
        #everything but WRLD and CELL
        self.interestingTopGroups = [b"GMST",b"GLOB",b"CLAS",b"FACT",b"HAIR",b"EYES",b"RACE",b"SOUN",b"SKIL",b"MGEF",b"SCPT",b"LTEX",b"ENCH",b"SPEL",b"BSGN",b"ACTI",b"APPA",b"ARMO",b"BOOK",b"CLOT",b"CONT",b"DOOR",b"INGR",b"LIGH",b"MISC",b"STAT",b"GRAS",b"TREE",b"FLOR",b"FURN",b"WEAP",b"AMMO",b"NPC_",b"CREA",b"LVLC",b"SLGM",b"KEYM",b"ALCH",b"SBSP",b"SGST",b"LVLI",b"WTHR",b"CLMT",b"REGN",b"DIAL",b"QUST",b"IDLE",b"PACK",b"CSTY",b"LSCR",b"LVSP",b"ANIO",b"WATR",b"EFSH",]

    def readRecord(self):
        #consume and return one whole record. Leaves file pointer at end of record.
        #Todo: handle flags

        self.debug(self.ftell())
        _type, dataSize, flags, formid, vcinfo = struct.unpack(recordStruct, self.file.read(20))

        self.debug(_type)

        assert _type != b'GRUP' #accidentally read group as record - programming error
        if flags & 262144: #compressed
            decompressedDataSize = struct.unpack("L",self.file.read(4))
            # print('debug decomp size: '+ str(decompressedDataSize))
            # print(self.ftell())
            # print(dataSize)
            tmp = zlib.decompress(self.file.read(dataSize-4))
            # import code
            # code.interact(local=locals())
            record = Record(_type, dataSize, flags, formid, vcinfo, self.subrecords(tmp))
            self.debug(self.ftell())
            return record
        else:
            record = Record(_type, dataSize, flags, formid, vcinfo, self.subrecords(self.file.read(dataSize)))
            self.debug(self.ftell())
            return record

    def readGroup(self, top=False):
        #consume and return group. 
        self.debug('readGroup start: '+self.ftell())
        _type, groupSize, label, groupType, stamp = struct.unpack(groupStruct, self.file.read(20))
        
        if top and label not in self.interestingTopGroups:
            self.file.seek(groupSize-20,1)
            return None

        contents = []

        contentsEnd = self.file.tell()+groupSize-20
        while self.file.tell() < contentsEnd:
            readahead = self.file.read(4)
            self.file.seek(-4,1)

            if readahead == b'GRUP':
                group = self.readGroup()
                # print(group.type)
                contents.append(group)
                # import code
                # code.interact(local=locals())
            else:
                record = self.readRecord()
                # print(record.type)
                contents.append(record)

            # print()

        return Group(_type,groupSize,label,groupType,stamp,contents)

    def subrecords(self,data):
        #generator that takes record data and returns subrecords
        srStart = 0
        largeSRSize = 0
        while True:
            if srStart == len(data):
                raise StopIteration #all subrecords processed
            if largeSRSize: #previous subrecord was a large subrecord marker
                record = Subrecord(*struct.unpack(subrecordStruct, data[srStart:srStart+6]), data[srStart+6:srStart+6+largeSRSize])
                srStart += 6+largeSRSize
                largeSRSize = 0
                yield record
                continue

            subType, dataSize = struct.unpack(subrecordStruct, data[srStart:srStart+6])
            record = Subrecord(subType, dataSize, data[srStart+6:srStart+6+dataSize])
            if subType == b'XXXX': #large subrecord marker
                largeSRSize = struct.unpack("L", record.data)[0] #data is size of next subrecord
                print('large subrecord type {} size {}'.format(data[srStart+10:srStart+14], largeSRSize))
                srStart += 6+dataSize
                continue
            srStart += 6+dataSize
            yield record
            continue

    def load(self):
        #actually read in the ESM data
        #I don't want to import os just for fstat
        self.file.seek(0,2)
        filesize = self.file.tell()
        self.file.seek(0)

        self.top = self.readRecord()
        
        while self.file.tell() < filesize:
            print('starting topgroup read')
            group = self.readGroup(top=True)
            if group:
                print("topGroup finished: " + group.label.decode())
            else:
                print('Group skipped.')
                continue
            
            self.groups.append(group)

    @staticmethod
    def debug(message):
        # print(inspect.stack()[1][3] + ": " + str(message))
        pass

    def ftell(self):
        return hex(self.file.tell())[2:]



        

#http://en.uesp.net/wiki/Tes4Mod:Mod_File_Format
recordStruct = "4s4L" #20 bytes
#type, dataSize, flags, formid, version control info
# Record = collections.namedtuple("Record", ('type', 'dataSize', 'flags', 'formid', 'vcinfo', 'subrecords'))

class Record(object):
    """docstring for Record"""
    def __init__(self, _type, dataSize, flags, formid, vcinfo, subrecords):
        super(Record, self).__init__()
        self.type = _type
        self.dataSize = dataSize
        self.flags = flags
        self.formid = formid
        self.vcinfo = vcinfo
        self.subrecords = subrecords

    def __repr__(self):
        return "Record: "+self.type.decode()


groupStruct = "4sL4slL" #20 bytes
#type, groupSize, label, groupType, stamp
# Group = collections.namedtuple("Group", ('type', 'groupSize', 'label', 'groupType', 'stamp', 'contents'))

class Group(object):
    """docstring for Group"""
    def __init__(self, _type, groupSize, label, groupType, stamp, contents):
        super(Group, self).__init__()
        self.type = _type
        self.groupSize = groupSize
        self.label = label
        self.groupType = groupType
        self.stamp = stamp
        self.contents = contents
        self.subgroups = [x for x in self.contents if x.type == b'GRUP']
        self.records =   [x for x in self.contents if x.type != b'GRUP']

    def __repr__(self):
        return "<GRUP: {}sg/{}r>".format(len([x for x in self.contents if x.type == b"GRUP"]),
                                         len([x for x in self.contents if x.type != b"GRUP"]))
    def __len__(self):
        return len(self.contents)

    def __iter__(self):
        for n in range(len(self)):
            yield self[n]

    def __getitem__(self, key):
        return self.contents[key]
        


subrecordStruct = "4sH" #6 bytes
#subType, dataSize
Subrecord = collections.namedtuple("Subrecord", ('type', 'dataSize', 'data'))




def openESM(f):
    #Given a file-like object or file path, returns an ESM object for that file
    if not isinstance(f, io.BytesIO):
        f = open(f, 'rb')

    return ESM(f)

