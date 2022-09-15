
import struct
import zlib
import xml.etree.ElementTree as ET
import ntpath
import os
import sys

import commands

LOAD_FLAGS_TIME = 0x1
LOAD_FLAGS_CAMERA1 = 0x2
LOAD_FLAGS_CAMERA2 = 0x4
LOAD_FLAGS_CAMERA3 = 0x8
LOAD_FLAGS_CAMERA46 = 0x10
LOAD_FLAGS_COMMANDS = 0x20 #might actually be COMMANDS_FEW or smth like that
LOAD_FLAGS_SELECTED_UNITS = 0x80

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

class RcxReader:
    decomp = None
    seek = 0
    is_ee = True

    def __init__(self, filepath, is_ee=True):
        # Read the data
        with open(filepath, "rb") as f:
            all = f.read()

        # Last sixteen raw bytes are a magic footer along with some data
        last_sixteen = all[-16:]
        if last_sixteen[:2] != b'RG' or last_sixteen[4:8] != b'\xd2\x02\x96I':
            raise ValueError("BAD footer")
        self.uncompressed_seek = struct.unpack("<I", last_sixteen[8:12])[0]
        self.field_18 = struct.unpack("<I", last_sixteen[0xc:])[0]


        # Check the header magic
        magic = all[:4]
        if magic != b"l33t":
            raise ValueError("Bad magic value")
        
        
        size = struct.unpack("<I", all[4:8])[0]
        rest = all[8:]

        # Decompress data
        try:
            decomp = zlib.decompress(rest)
        except zlib.error as e:
            raise ValueError("Recording corrupt")
        # Sanity check size
        if size != len(decomp):
            raise ValueError("Error in decompression. File might be corrupted")
        
        # Setup vars
        self.decomp = decomp
        
        # This seek is so late because there is a ton of stuff read into global config vars
        # This happens due to World::readStuff_likeCommandsActions (0x67fca0)
        # AFAIK, none of the config stuff seems relevant for the case of rcx's
        self.seek = 1474 if is_ee else 1466 # non ee should be checked

        self.is_ee = is_ee
        self.field_8 = 3 # This actually comes from some data. Should probably fix this at some point
    

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
        self.seek += 1
        return data
    def read_n(self,n):
        data = self.decomp[self.seek:self.seek+n]
        self.seek += n
        return data
    def read_four_s(self):
        data = struct.unpack("<i", self.decomp[self.seek:self.seek+4])[0]
        self.seek += 4
        return data

    def read_camera(self, loadFlags):
        if loadFlags & LOAD_FLAGS_CAMERA1:
            self.read_four()
        if loadFlags & LOAD_FLAGS_CAMERA2:
            self.read_four()
        if loadFlags & LOAD_FLAGS_CAMERA3:
            self.read_four()
        if loadFlags & LOAD_FLAGS_CAMERA46:
            self.read_n(0xc)    
            self.read_n(0xc)
            self.read_n(0xc)
        return

    def get_update_time(self, loadFlags):
        if loadFlags & LOAD_FLAGS_TIME:
            up_time = self.read_one()
        else:
            up_time = self.read_four()
        return up_time
    
    def read_num_commands(self, loadFlags):
        if loadFlags & LOAD_FLAGS_COMMANDS:
            return self.read_one()
        if loadFlags & 0x40 == 0:
            return 0
        return self.read_four()

    def get_command(self, loadFlags):
        test = self.read_one()
        if test != 0:
            cmd_type = self.read_four()
            cmd = commands.Command.get_command(cmd_type)
            cmd.read(self)

    def get_sync(self, loadFlags):
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
            decider = self.read_one()
            if decider != 0:
                self.read_sync_update()
            # print("Decider "+ str(decider))
    def read_sync_update(self):
        if self.is_ee:
            numSyncDatas = self.read_four()

            for i in range(numSyncDatas):
                first = self.read_one()
                self.read_one()
                self.read_two()
                if first & 0xf != 0x5:
                    self.read_four()
                self.read_four()
                self.read_four()
            ar = self.read_four()
            for i in range(ar):
                self.read_four()
        else:
            raise NotImplementedError("Non ee sync not yet implemented")
    
    def read_posVector(self):
        return [self.read_four(), self.read_four(), self.read_four()]

    def skip(self, n):
        self.seek += n

    def read_section(self, totalSize, blockSize):
        read = b""
        while totalSize > 0:
            toRead = min(totalSize, blockSize)
            read += self.read_n(toRead)
            totalSize -= toRead
            if totalSize > 0:
                self.seek += 4
        return read
    
    def read_file(self):
        totalSize = self.read_four()
        blockSize = self.read_four()
        return self.read_section(totalSize, blockSize)

class Player:
    gods = ["Zeus", "Poseidon", "Hades", "Isis", "Ra", "Set", "Odin", "Thor", "Loki", "Kronos", "Oranos", "Gaia", "Fu Xi", "Nu Wa", "Shennong", "4", "5", "6", "7", "8", "9", "10", "Nature", "12", "13", "14", "15", "16"]
    def __init__(self, civ, team, idx):
        self.civ = civ
        self.team = team
        self.idx = idx
        self.name = ""

    def setName(self, name):
        self.name = name

    def __str__(self):
        return self.name + "(" + self.gods[self.civ] + ")"

    def __repr__(self):
        return self.__str__()
allplayers = []

class Update:
    def __init__(self, commands, selectedUnits, time):
        self.commands = commands
        self.selectedUnits = selectedUnits
        self.time = time
        self.num = -1

    def set_num(self, num):
        self.num = num

class Rec:
    def __init__(self, filepath):
        self.players = []
        self.filepath = filepath
        # Create our RcxReader
        self.reader = RcxReader(filepath)
        self.updates = []
        
    def parse_update(self):
        selectedUnits = []
        commands = []

        loadFlags = self.reader.read_one()
        if loadFlags & 0x40:
            # Haven't seen yet, don't know how to handle for sure
            # Might be missing some stuff. It might also just work.  
            raise ValueError("ERROR LOADFLAGS") 

        self.reader.read_camera(loadFlags)

        upTime = self.reader.get_update_time(loadFlags)

        # Read the commands
        numCommands = self.reader.read_num_commands(loadFlags)
        commands = [None] * numCommands
        for i in range(numCommands):
            commands[i] = self.reader.get_command(loadFlags)

        # Read the selected units
        if loadFlags & LOAD_FLAGS_SELECTED_UNITS:
            numUnits = self.reader.read_one()
            selectedUnits = [0] * numUnits
            for i in range(numUnits):
                selectedUnits[i] = self.reader.read_four()
        
        
        # Haven't looked into what this is
        # I *think* it's a bunch of unitIds used for something
        smth = self.reader.read_one()
        for i in range(smth):
            self.reader.read_one()


        # byte read from header field_4c

        # Read sync info
        self.reader.get_sync(loadFlags)

        
        if self.reader.field_8 < 1:
            # self.validate_read()
            pass
        return Update(commands, selectedUnits, upTime)
    
    def parse_header(self):
        # read game settings (lastGameSettings.xml)
        lastGameXml = self.reader.read_file()          
        self.xml = lastGameXml.decode("utf-16")

        
        # read map script (recordGameRandomMap.xs)
        self.recordGameMap = self.reader.read_file()
        
        # Read info about the players (civ, team)
        numPlayers = self.reader.read_four()
        for i in range(numPlayers):
            playerCiv = self.reader.read_four()
            playerTeam = self.reader.read_four()
            
            curPlayer = Player(playerCiv, playerTeam, i-1)
            self.players.append(curPlayer)
        
        # Match players we just read with players from Xml File
        # This lets us find attributes such as the player name
        root = ET.fromstring(self.xml)
        for player_ele in root.findall("Player"):
            if 'ClientIndex' in player_ele.attrib:
                idx = player_ele.attrib['ClientIndex']
            else:
                idx = player_ele.attrib['ClientID']
            player = self.players[int(idx)+1]
            name = player_ele.find("Name").text 
            if name is not None:
                player.setName(player_ele.find("Name").text )
        
        global allplayers
        allplayers = self.players

        # Skip 1 + 4 + 4 + 4 bytes found after the civ,team info
        self.reader.skip(9)
        self.reader.skip(4)

        # Read the difficulty, player number
        self.difficulty = self.reader.read_four()
        plNum2 = self.reader.read_four()
        
        # For every player read some more info about them
        for i in range(plNum2):
            read_player = self.reader.read_one()
            if read_player == 0:
                continue
            self.reader.skip(4)
            
            teamId = self.reader.read_four()
            sz = self.reader.read_four()
            teamDesc = self.reader.read_n(sz)
            print(teamDesc)

            newNum = self.reader.read_four() #might be color stuff, can't remember
            for i in range(newNum):
                data = self.reader.read_four()


        # We now read more info about the players.
        # Not exactly sure what all this is
        # In there is civ, culture, and maybe the default stance
        # Also in there is the starting relation with other players
        # Some color info too
        alsoNumPlayers = self.reader.read_four()
        if alsoNumPlayers != numPlayers:
            raise ValueError("ERROR. alsoNumPlayers doesn't match")

        for i in range(alsoNumPlayers):
            tester = self.reader.read_one()

            if tester == 0:
                continue
            check_3f = self.reader.read_four_s()
            god_flags_idk_dude = self.reader.read_one()
            god_flags_idk_dude = self.reader.read_one()
            maybe_stance = self.reader.read_four()


            # sub_512b30

            some = self.reader.read_four()
            more = self.reader.read_n(2*some)

            field_10 = self.reader.read_four()
            type_flags = self.reader.read_one()

            culture = self.reader.read_four()
            civ = self.reader.read_four()

            field_18 = self.reader.read_four()
            field_4b4 = self.reader.read_four()
            field_4b8 = self.reader.read_four()
            if check_3f >= 0x3f:
                test2 = self.reader.read_four_s()
                if test2 > 0x10:
                    print("PL NUM ERR")
                    return
                if test2 > 0:
                    for i in range(test2):
                        rel = self.reader.read_four()
            colors = self.reader.read_four()
    

    def parse(self):
        self.parse_header()
        
        # Now we parse all the updates
        for updateNum in range(1,0x10000):
            pre = self.reader.seek
            update = self.parse_update()
            update.num = updateNum
            self.updates.append(update)
            if updateNum % 5000 == 0:
                print("Seek after update #" + str(updateNum) + " = " + hex(self.reader.seek) + " / " + hex(len(self.reader.decomp)) + "     " + str(self.reader.seek/len(self.reader.decomp)) + "%      "+ str(self.reader.seek-pre))
            if len(self.reader.decomp) == self.reader.seek:
                break
        print("Finished reading everything!")

        # This stuff isn't currently used. this is the reading of the syncBobbers
        # It happens some time before the updates, but doesn't seem to be important
        # we now are not reading compressed
        # just read direct
        # syncBobberRead = reader.read_four()
        # for i in range(syncBobberRead):
        #     syncBobberData = reader.read_four()
        # now back to compressed at same seek

    def display_by_teams(self):
        teams = [[] for i in range(len(self.players))]
        for player in self.players:
            if player.team <= 0: #handles obs i think
                continue
            else:
                team = teams[player.team]
                team.append(player)
        
        for team in teams:
            if len(team) > 0:
                print("\tTeam " + str(team[0].team)+": ",end="")
                for player in team:
                    print(str(player) + " ",end="")
                print()

    def get_display_string(self):
        teams = [[] for i in range(len(self.players))]
        for player in self.players:
            if player.team <= 0: #handles obs i think
                continue
            else:
                team = teams[player.team]
                team.append(player)
        
        ret = ""
        for team in teams:
            if len(team) > 0:
                ret += ("\tTeam " + str(team[0].team)+": ")
                for player in team:
                    ret+= (str(player) + " ")
                ret += "\n"

        return ret

def main():
    # base_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Age of Mythology\\savegame\\"
    # # base_path = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"
    # fd = open("recs.txt", "w")
    # for file in os.listdir(base_path):
    #     if file.endswith(".rcx"):
    #         try:
    #             print(file)
    #             rec = Rec(base_path + file)
    #             rec.display_by_teams()
    #             fd.write(file + "\n")
    #             fd.write(rec.get_display_string())
    #         except Exception as e:
    #             print(e)            
    # fd.close()

#    Rec("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"+"Replay v2.8 @2020.07.16 234459.rcx").display_by_teams()
    # Rec("/mnt/c/Users/stnevans/Downloads/nube1978_cheat.rcx").display_by_teams()
    # Rec("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"+"t_Replay v2.8 @2020.11.15 183223.rcx").display_by_teams()
    # Rec("C:\Program Files (x86)\Steam\steamapps\common\Age of Mythology\savegame\")
    rec = Rec("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"+"Replay v2.8 @2022.09.10 005123.rcx")
    rec.parse()
    rec.display_by_teams()
    print(rec.updates)
    # Rec("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"+"son_of.rcx").display_by_teams()

if __name__ == '__main__':
    main()