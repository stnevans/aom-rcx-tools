import zlib
import struct
import os
import argparse
import xml.etree.ElementTree as ET

import commands as Commands

LOAD_FLAGS_TIME = 0x1
LOAD_FLAGS_CAMERA1 = 0x2
LOAD_FLAGS_CAMERA2 = 0x4
LOAD_FLAGS_CAMERA3 = 0x8
LOAD_FLAGS_CAMERA46 = 0x10
LOAD_FLAGS_COMMANDS_FEW = 0x20
LOAD_FLAGS_COMMANDS_MANY = 0x40
LOAD_FLAGS_SELECTED_UNITS = 0x80


class ObsAdd:
    
    def __init__(self, filepath, is_ee, observer_name):
        with open(filepath, "rb") as f:
            all = f.read()
        
        # Check the header magic
        magic = all[:4]
        if magic != b"l33t":
            raise ValueError("Bad magic value")
        
        size = struct.unpack("<I", all[4:8])[0]
        rest = all[8:]
        decomper = zlib.decompressobj()
            
        # Decompress data
        try:
            decomp = decomper.decompress(rest)
        except zlib.error as e:
            raise ValueError("Recording corrupt")
        # Sanity check size
        if size != len(decomp):
            raise ValueError("Error in decompression. File might be corrupted")
        self.decomp = decomp
        
        self.seek = 1474 if is_ee else 1466
        self.outpath = filepath[:-4] + "_obs.rcx"
        # self.outpath = "rcxs/test.rcx"
        self.footer = decomper.unused_data
        
        self.out_str = b""
        self.write_data(self.decomp[:self.seek])

        last_sixteen = all[-16:]
        uncompressed_seek = struct.unpack("<I", last_sixteen[8:12])[0]

        self.is_ee = is_ee
        self.observer_name = observer_name

    def skip(self, n):
        self.seek += n

    def read_section(self, totalSize):
        read = b""
        while totalSize > 0:
            blockSize = self.read_four()
            if blockSize == 0:
                raise ValueError("Zero block size")
            toRead = min(totalSize, blockSize)
            read += self.read_n(toRead)
            totalSize -= toRead
        return read
    
    def read_file(self):
        totalSize = self.read_four()
        return self.read_section(totalSize)

    def read_four(self):
        data = struct.unpack("<I", self.decomp[self.seek:self.seek+4])[0]
        self.seek += 4
        return data
    def read_one(self):
        data = struct.unpack("B", self.decomp[self.seek:self.seek+1])[0]
        self.seek += 1
        return data
    def read_two(self):
        data = struct.unpack("H", self.decomp[self.seek:self.seek+2])[0]
        self.seek += 2
        return data
    def read_n(self,n):
        data = self.decomp[self.seek:self.seek+n]
        self.seek += n
        return data
    def read_four_s(self):
        data = struct.unpack("<i", self.decomp[self.seek:self.seek+4])[0]
        self.seek += 4
        return data

    def read_posVector(self):
        return [self.read_four(), self.read_four(), self.read_four()]

    def read_and_write_four(self):
        data = self.read_four()
        self.write_four(data)
        return data
    def read_and_write_n(self, n):
        data = self.read_n(n)
        self.write_data(data)
        return data

    def read_and_write_one(self):
        data = self.read_one()
        self.write_one(data)
        return data

    def read_and_write_four_s(self):
        data = self.read_four_s()
        self.write_four_s(data)
        return data
    def read_and_write_two(self):
        data = self.read_two()
        self.write_two(data)
        return data
    def write_two(self, data):
        self.out_str += struct.pack("H", data)
    def write_four(self, ourInt):
        self.out_str += struct.pack("<I", ourInt)
    
    def write_four_s(self, ourInt):
        self.out_str += struct.pack("<i", ourInt)
    
    def write_data(self, data):
        self.out_str += data

    def write_one(self, data):
        self.out_str += struct.pack("B", data)
    
    def write_file(self, data):
        size = len(data)
        self.write_four(size)
        toWrite = size
        i = 0
        while toWrite > 0:
            blockSize = min(toWrite, 1024)
            self.write_four(blockSize)
            self.write_data(data[i:i+blockSize])

            toWrite -= blockSize
            i += blockSize

    def read_and_write_camera(self, loadFlags):
        if loadFlags & LOAD_FLAGS_CAMERA1:
            self.read_and_write_four()
        if loadFlags & LOAD_FLAGS_CAMERA2:
            self.read_and_write_four()
        if loadFlags & LOAD_FLAGS_CAMERA3:
            self.read_and_write_four()
        if loadFlags & LOAD_FLAGS_CAMERA46:
            self.read_and_write_n(0xc)    
            self.read_and_write_n(0xc)
            self.read_and_write_n(0xc)
        return

    def read_and_write_update_time(self, loadFlags):
        if loadFlags & LOAD_FLAGS_TIME:
            up_time = self.read_and_write_one()
        else:
            up_time = self.read_and_write_four()
        return up_time
    
    def read_num_commands(self, loadFlags):
        if loadFlags & LOAD_FLAGS_COMMANDS_FEW:
            return self.read_one()
        if loadFlags & LOAD_FLAGS_COMMANDS_MANY == 0:
            return 0
        return self.read_four()

    def read_and_write_command(self, loadFlags):
        test = self.read_and_write_one()
        if test != 0:
            cmd_type = self.read_and_write_four()
            before = self.seek
            cmd = Commands.Command.get_command(cmd_type) #TODO
            cmd.read(self)
            afterseek = self.seek
            self.write_data(self.decomp[before:afterseek])
            return cmd
        return None

    def read_and_write_sync(self, loadFlags):
        if self.is_ee:
            field_4c = 1
            do_it = False
            if self.field_8 < 1:
                do_it = True
            elif self.field_8 < 2:
                if loadFlags < 128:
                    do_it = True
            else:
                if field_4c != 0:
                    do_it = True
            if do_it:
                decider = self.read_and_write_one()
                if decider != 0:
                    self.read_and_write_sync_update()
        else:
            if self.field_8 >= 2:
                return
            raise NotImplementedError("Field 8 weird")

    def read_and_write_sync_update(self):
        numSyncDatas = self.read_and_write_four()

        for i in range(numSyncDatas):
            first = self.read_and_write_one()
            self.read_and_write_one()
            self.read_and_write_two() #todo this was bugged i need to check
            if first & 0xf != 0x5:
                self.read_and_write_four()
            self.read_and_write_four()
            self.read_and_write_four()
        ar = 0
        # self.write_four(0)
        ar = self.read_and_write_four()
        for i in range(ar):
            # self.read_four()
            # self.write_four(0)
            self.read_and_write_four()
    
    def write_resign_command(self, playerId, resignerId):
        self.write_one(1)
        self.write_four(0x14) # write type
        # Start writing command
        # type
        # base = b'\x14\x01\x00\x00\x00'
        # +b'\xff\xff\xff\xff\xff\xff\xff\xff\x03\x00\x00\x00\x01\x00\x00\x00'
        # +b'\x01\x00\x00\x00'
        # +b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        # +b'\xff\xff\xff\xff\xff\xff\xff\xff\x03\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00'
        self.write_one(0x14) #id
        self.write_four(playerId) # pl id
        self.write_data(b'\xff\xff\xff\xff\xff\xff\xff\xff\x03\x00\x00\x00\x01\x00\x00\x00')
        self.write_four(playerId)
        self.write_data(b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.write_data(b'\xff\xff\xff\xff\xff\xff\xff\xff')
        self.write_four(resignerId)
        self.write_four(playerId) 
        self.write_four(self.obs_id) # total players
        # self.write_four(0xffffffff)
        # self.write_four(0xffffffff)

    def parse_update_and_add_resign_commands(self, do_add_command):
        selectedUnits = []
        commands = []

        loadFlags = self.read_one()
        oldFlags = loadFlags
        if loadFlags & LOAD_FLAGS_COMMANDS_MANY:
            raise NotImplementedError("Haven't implemented lots of commands in one update yet")
        if do_add_command:
            oldFlags = loadFlags
            loadFlags |= LOAD_FLAGS_COMMANDS_FEW
            # print(hex(loadFlags),("After header seek =", hex(len(self.out_str))))

        self.write_one(loadFlags)

        self.read_and_write_camera(loadFlags)

        upTime = self.read_and_write_update_time(loadFlags)
        
        if oldFlags & LOAD_FLAGS_COMMANDS_FEW:
            # Read the commands
            numCommands = self.read_num_commands(loadFlags)
        else:
            numCommands = 0
        # commands = [None] * numCommands
        if do_add_command:
            # We just write ourself a resign command in this case

            # self.write_one(numCommands + self.obs_id)
            self.write_one(numCommands + 1)
            self.write_resign_command(1, self.obs_id)
            # for i in range(1, self.obs_id+1): 
            #     self.write_resign_command(i, self.obs_id)
            # print(hex(loadFlags),("After header seek =", hex(len(self.out_str))))
        else:
            if oldFlags & LOAD_FLAGS_COMMANDS_FEW:
                self.write_one(numCommands)
        

        for i in range(numCommands):
            cmd = self.read_and_write_command(loadFlags) #TODO
            # cmd = commands[i]


        # Read the selected units
        if loadFlags & LOAD_FLAGS_SELECTED_UNITS:
            numUnits = self.read_and_write_one()
            selectedUnits = [0] * numUnits
            for i in range(numUnits):
                selectedUnits[i] = self.read_and_write_four()
        
        
        # This seems to be the affected player ids
        if not do_add_command:
            smth = self.read_and_write_one()
            for i in range(smth):
                self.read_and_write_one()
        else:
            # write ourself as an affected player (by the resign command)
            smth = self.read_one()
            self.write_one(smth+1)
            self.write_one(self.obs_id)
            for i in range(smth):
                self.read_and_write_one()
            
        # # byte read from header field_4c

        # # Read sync info
        self.read_and_write_sync(loadFlags)

        # if self.field_8 < 1:
        #     # self.validate_read()
        #     pass
        
    def add_obs(self):
        lastGameSettingsXml = self.read_file()
        
        self.xml = lastGameSettingsXml.decode("utf-16")
        
        root = ET.fromstring(lastGameSettingsXml)
        realNumPlayers = int(root.find("NumPlayers").text)
        newRealNumPlayers = realNumPlayers+1

        root.find("NumPlayers").text = str(realNumPlayers+1)
        obs = ET.Element("Player")
        if self.is_ee:
            obs.attrib["ClientIndex"] = str(newRealNumPlayers-1)    
        else:
            obs.attrib["ClientID"] = str(newRealNumPlayers-1)    

        obs.attrib["ControlledPlayer"] = str(newRealNumPlayers)
        name_ele = ET.SubElement(obs, "Name")
        name_ele.text = self.observer_name


        rating_ele = ET.SubElement(obs, "Rating")
        rating_ele.text = "2800.000000"

        type_ele = ET.SubElement(obs, "Type")
        type_ele.text = "4" # This is observer type

        ET.SubElement(obs, "TransformColor1").text = "0"
        ET.SubElement(obs, "TransformColor2").text = "0"
        ET.SubElement(obs, "Team").text = "255"
        ET.SubElement(obs, "Civilization").text = "1"
        ET.SubElement(obs, "AIPersonality")
        

        # gameSettings = root.find("GameSettings")
        root.append(obs)
        # ET.indent(root, space="\t", level=0)

        new_root = ET.tostring(root, encoding= "utf-16", xml_declaration=False)
        
        with open("rcxs/lastGame.xml", 'wb') as f:
            f.write(new_root)
        # testing = b"A"*0x1000

        self.write_file(new_root)

        # read map script (recordGameRandomMap.xs)
        self.recordGameMap = self.read_file()
        self.write_file(self.recordGameMap)

        # Read info about the players (civ, team)
        numPlayers = self.read_four()
        self.obs_id = numPlayers
        if numPlayers != realNumPlayers + 1:
            raise ValueError("Doesn't match")
        newNumPlayers = numPlayers + 1
        self.write_four(newNumPlayers)
        for i in range(numPlayers):
            self.write_four(self.read_four())
            self.write_four(self.read_four())
        # Write the civ, team for our new obs
        self.write_four(1)
        self.write_four(0xffffffff) # team -1
        
        # Can't remember what this is
        # Done by   AGame::doesSomeGsRead
        self.write_data(self.read_n(13))
        self.write_four(self.read_four())

        numTeams = self.read_four()
        self.write_four(numTeams)
        for i in range(numTeams):
            read_player = self.read_and_write_one()
            if read_player == 0:
                continue
            self.read_and_write_four()
            

            teamId = self.read_and_write_four()
            sz = self.read_and_write_four()
            teamDesc = self.read_and_write_n(sz)
            newNum = self.read_and_write_four() #might be color stuff, can't remember
            for i in range(newNum):
                data = self.read_and_write_four()

        alsoNumPlayers = self.read_four()
        if alsoNumPlayers != numPlayers:
            raise ValueError("Num players check")

        self.write_four(newNumPlayers)
        for i in range(alsoNumPlayers):
            tester = self.read_and_write_one()

            if tester == 0:
                continue
            check_3f = self.read_and_write_four_s()
            god_flags_idk_dude = self.read_and_write_one()
            god_flags_idk_dude2 = self.read_and_write_one()
            maybe_stance = self.read_and_write_four()


            # sub_512b30

            some = self.read_and_write_four()
            more = self.read_and_write_n(2*some)

            field_10 = self.read_and_write_four()
            type_flags = self.read_and_write_one()

            culture = self.read_and_write_four()
            civ = self.read_and_write_four()

            field_18 = self.read_and_write_four() #seems to be team again
            field_4b4 = self.read_and_write_four()
            field_4b8 = self.read_and_write_four()
            if check_3f >= 0x3f:
                test2 = self.read_and_write_four_s()
                if test2 > 0x10:
                    print("PL NUM ERR")
                    return
                if test2 > 0:
                    for j in range(test2):
                        rel = self.read_and_write_four()
            colors = self.read_and_write_four()

        # Now we write a new player
        self.write_one(1)
        self.write_four_s(75)
        self.write_one(0) # flags 1
        self.write_one(0) #flags 2
        self.write_four(0) # stance
        # name = "Stu was here".encode("utf-16")[2:]
        name = self.observer_name.encode("utf-16")[2:]
        self.write_four(len(name)//2)
        print("Adding observer \"" + str(self.observer_name) +"\"")
        self.write_data(name)
        self.write_four(0)
        self.write_one(4)
        self.write_four(2) # culture
        self.write_four(6) # civ 
        self.write_four(0xffffffff) # team thing
        self.write_four(1065353216) # test this TODO
        self.write_four(0)

        # now we write relations
        self.write_four_s(16)
        for i in range(16):
            if i == self.obs_id:
                self.write_four(0)
            else:
                self.write_four(2) 

        self.write_four(3) # color


        # We have now added a player that is an observer named Stu
        # What we must next do is create resign commands, 1 for each player with the resigningPlayerId == self.obs_id
        # print(self.obs_id)
        self.field_8 = 3
        for i in range(4):
            self.parse_update_and_add_resign_commands(False)
        self.parse_update_and_add_resign_commands(True)
        self.write_out()


    def write_out(self):
        data = self.out_str + self.decomp[self.seek:]
        compressed = zlib.compress(data)
        with open(self.outpath, 'wb') as f:
            f.write(b"l33t")
            f.write(struct.pack("<I", len(data))) # WE NEED TO FIX THE SYNC BOBBER STUFF
            f.write(compressed)
            loc = len(b"l33t") + 4 + len(compressed)
            loc_bytes = struct.pack("<I", (loc))
            
            # print(self.footer, self.footer[-8])
            # The area at uncompressed seek loc determines the seek used.
            # It looks like the following:
            # 0xloc: numberSyncCategories
            # 0xloc+4 ... 0xloc+4*(i in numberSyncCategories): categoryEnabled
            # So we disable all sync categories
            num_sync_categories = 0x1a
            if struct.unpack("<I", self.footer[:4])[0] != num_sync_categories:
                print("Bad number sync categories, prob AoT. Sadly this will probably OOS")
                num_sync_categories = struct.unpack("<I", self.footer[:4])[0]
                footer_data = struct.pack("<I", num_sync_categories)
                for i in range(num_sync_categories):
                    footer_data += struct.pack("<I", 0)
                print(footer_data)
                print(self.footer[:-16])
            else:
                footer_data = struct.pack("<I", num_sync_categories)
                for i in range(num_sync_categories):
                    footer_data += struct.pack("<I", 0)
            footer_data += self.footer[len(footer_data):-8]
            
            new_footer = footer_data + loc_bytes + self.footer[-4:]

            f.write(new_footer)
        print("Saved to " + self.outpath)

        
# ObsAdd("rcxs/momo_vs_kvoth_1_.rcx", is_ee=False).add_obs()
# ObsAdd("rcxs/3ppl.rcx", is_ee=True).add_obs()

parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('observer_name', default="Observer(Stu)", nargs="?")
args = parser.parse_args()
ObsAdd(args.filename, is_ee=True, observer_name=args.observer_name).add_obs()

AOM_PATH = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/"
# ObsAdd(AOM_PATH+os.sep+"savegame"+os.sep+"Replay v2.8 @2020.11.15 190728.rcx", is_ee=True).add_obs()
