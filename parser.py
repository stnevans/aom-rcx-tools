
import struct
import zlib
import xml.etree.ElementTree as ET
import ntpath
import os
import sys
import argparse

import commands as Commands


AOM_PATH = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/"
AOM_VERSION = "2.8"


LOAD_FLAGS_TIME = 0x1
LOAD_FLAGS_CAMERA1 = 0x2
LOAD_FLAGS_CAMERA2 = 0x4
LOAD_FLAGS_CAMERA3 = 0x8
LOAD_FLAGS_CAMERA46 = 0x10
LOAD_FLAGS_COMMANDS_FEW = 0x20
LOAD_FLAGS_COMMANDS_MANY = 0x40
LOAD_FLAGS_SELECTED_UNITS = 0x80

PLAYER_TYPE_OBS = 4
PLAYER_TYPE_HUMAN = 0
PLAYER_TYPE_COMP = 1

START_LAST_TEAM_ID = -3
class CivManager:
    def __init__(self, is_ee):
        ee_gods = ["Zeus", "Poseidon", "Hades", "Isis", "Ra", "Set", "Odin", "Thor", "Loki", "Kronos", "Oranos", "Gaia", "Fu Xi", "Nu Wa", "Shennong", "4", "5", "6", "7", "8", "9", "10", "Nature", "12", "13", "14", "15", "16"]
        aot_gods = ["Zeus","Poseidon", "Hades", "Isis", "Ra", "Set", "Odin", "Thor", "Loki", "Kronos", "Oranos", "Gaia", "2", "3", "4", "5", "6", "Nature"]
        EE_NATURE_CIV = 22
        AOT_NATURE_CIV = 17

        if is_ee:
            self.gods = ee_gods
            self.nature_idx = EE_NATURE_CIV
        else:
            self.gods = aot_gods
            self.nature_idx = AOT_NATURE_CIV

    def get_god(self, civ_idx):
        return self.gods[civ_idx]

    def get_nature_idx(self):
        return self.nature_idx

class ProtoUnitDatabase:
    def __init__(self):
        proto_unit_path = AOM_PATH + os.sep + "data" + os.sep + "proto" + AOM_VERSION + ".xml"
        tree = ET.parse(proto_unit_path)
        self.tree = tree
        self.units = tree.findall("unit")
        # Language path for translating displayid
        en_lang_path = AOM_PATH + os.sep + "Language" + os.sep + "en" + os.sep + "en-language.txt"
        with open(en_lang_path, 'r', encoding="utf-16-le") as f:
            lang_lines = f.readlines()
        self.display_map = {}
        for line in lang_lines:
            tokens = line.split()
            if len(tokens) > 1:
                if tokens[0].isdigit():
                    display_id = int(tokens[0])
                    text = line[len(tokens[0]):].strip()
                    self.display_map[display_id] = text[1:-1]
                
    
    def get_name(self, id):
        for unit in self.units:
            if int(unit.attrib["id"]) == id:
                return unit.attrib["name"]

    def get_displayname(self, id):
        for unit in self.units:
            if int(unit.attrib["id"]) == id:
                display_id = int(unit.find("displaynameid").text)
                return self.display_map[display_id]
class TechTreeDatabase:
    # Tech tree uses an odd format for ids
    # It doesn't store the actual id. DBID is not used as the tech id
    # Instead its just the order of techs in the file. 
    # e.g. the first tech in the file has an id of 0

    def __init__(self):
        self.techs = []
        tech_tree_path = AOM_PATH + os.sep + "data" + os.sep + "techtree" + AOM_VERSION + ".xml"
        with open(tech_tree_path, 'r') as f:
            for line in f:
                if "tech name=".lower() in line.lower():
                    startFind = "name="
                    endFind = "type="
                    self.techs.append(line[line.find(startFind)+len(startFind)+1:line.find(endFind)-2])

    def get_tech(self, id):
        return self.techs[id]

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

class RcxReader:
    decomp = None
    seek = 0
    is_ee = True

    def __init__(self, filepath):
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
        

        self.field_8 = self.read_four() # Should always be 3
        if not self.field_8 == 3:
            raise NotImplementedError("Field 8 not 3. We haven't really supported this")

        cur_time = self.read_four()
        v20 = self.read_four()
        field_4c = self.read_one()
        v54 = self.read_four()

        field_14 = self.read_four()
        v58 = self.read_four()

        v3c0 = self.read_four()
        field_e0 = self.read_one()

        field_104 = self.read_four()
        
        v3b5 = self.read_one()
        if v3b5 != 0:
            n = self.read_four()
            # TODO
            # AFAIK voobly puts a 25 here and ee puts a 26. Should be tested :)
            # Would let us automate is_ee which would be really nice
            # Looks like yes. this is sync stuff
            self.is_ee = (n==26)
            if n != 26:
                print("Detected AoT game (n=" + str(n) + ")")

            for i in range(n):
                self.read_four()
            a120 = self.read_four()
            n = self.read_four()
            # TODO
            # AFAIK voobly puts a 25 here and ee puts a 26. Should be tested :)
            # Would let us automate is_ee which would be really nice
            for i in range(n):
                self.read_four()
        v3b5 = self.read_one()
        if v3b5 != 0:
            n = self.read_four()
            for i in range(n):
                self.read_four()
            a120 = self.read_four()
            n = self.read_four()
            for i in range(n):
                self.read_four()
        
        self.f_54 = self.read_four() # Maybe is_restore
        if not self.f_54:
            v3d0 = self.read_four()

        # This seek is so late because there is a ton of stuff read into global config vars
        # This happens due to World::readStuff_likeCommandsActions (0x67fca0)
        # AFAIK, none of the config stuff seems relevant for the case of rcx's


        # World::readStuff_likeCommandsActions consumes 1210
        if self.f_54:
            self.parse_svx()
        self.seek = 1474 if self.is_ee else 1466 # non ee should be checked
        
        self.field_8 = 3 # This actually comes from some data. Should probably fix this at some point


    def readExpectedTag(self, expected_tag):
        real_tag = self.read_two()
        if real_tag != expected_tag:
            raise ValueError("Bad tag read")
        self.read_four()
    
    def read_2bytechecked_and4bytes(self, expected_tag):
        real_tag = self.read_two()
        if real_tag != expected_tag:
            raise ValueError("Bad tag read")
        return self.read_four()
    

    ### START SVX
    def sub_512b30(self): # I am read 4 then n
        n = self.read_four()
        if n > 0:
            data = (self.read_n(n*2))

    def sub_7c16a0(self):
        self.readExpectedTag(18242)
        savedgamereader_fc = self.read_four()
        if savedgamereader_fc < 0x19:
            raise NotImplementedError("Not encountered")
        self.sub_512b30()
        
        a5 = self.read_four()
        
        if a5 > 0:
            raise NotImplementedError("Also not yet")
        a3 = self.read_four()
        self.sub_512b30()
        return savedgamereader_fc


    def read_player_cfg_data(self, a3):
        type = self.read_one()
        color1 = self.read_one()
        color2 = self.read_one()
        civ = self.read_one()
        if a3 < 7:
            self.read_one()
        if a3 == 2:
            self.read_two()

    def read_world_cfg_data(self):
        v8 = self.read_four_s()
        if v8 < 9:
            player_read = 0x10
        else:
            player_read = 0x11
        for i in range(player_read):
            self.read_player_cfg_data(v8)
        if v8 <= 3:
            return
        numPlayers = self.read_four()
        seed = self.read_four()
        diff = self.read_four()
        if v8 >= 5:
            handicap = self.read_four()
        if v8 >= 6:
            gameplayMode = self.read_four()
        if v8 < 8:
            return
        teamCreateMode = self.read_four()

    def read_client_cfg_data_help(self, a3):
        some_n = self.read_four()
        if a3 >= 0xb:
            self.read_n(2 * some_n)
        else:
            raise NotImplementedError("a3 less than 0xb")
        if a3 != 3:
            if a3 >= 4:
                rating = self.read_four()
            if a3 >= 8:
                handicap = self.read_four()
            if (a3 - 9) > 3:
                return
            self.read_one()
            return
        self.read_two()

    def read_client_cfg_data(self, a3):
        self.read_client_cfg_data_help(a3)
        #back to MpClientConfigData::read

        if a3 >= 2:
            controlledPlayer = self.read_one()
        if a3 >= 7:
            team = self.read_one()

    def read_game_cfg_data(self):
        v8 = self.read_four()
        i = 0
        while True:
            self.read_client_cfg_data(v8)
            i += 1
            if i >= 0x10:
                break
        if v8 >= 0xc:
            n = self.read_four()
            self.read_n(2 * n)
        if v8 >= 0xe:
            gameType = self.read_one()
            flagSettings = self.read_four()
            numPauses = self.read_one()
            mapSize = self.read_one()
            vis = self.read_one()
            worldRes = self.read_one()
            aiDiff = self.read_one()
        if v8 >= 0xf:
            treatyLen = self.read_one()
        
    def create_and_read_config_datas(self):
        self.read_world_cfg_data()
        self.read_game_cfg_data()


    def sub_7c17e0(self):
        data = self.read_one()
        if data == 0:
            raise NotImplementedError("This is bad state I think")
        self.create_and_read_config_datas()
    
    def sub_4e24f0(self):
        return self.read_four()

    def sub_4e2310(self):
        if self.fc > 0x1b:
            self.sub_512b30()
            self.read_four()
            self.read_four()
            v118 = self.read_four()
            if self.fc >= 0xd:
                self.read_four()
            if self.fc < 0x1b:
                return
            arg2_1 =  self.read_four()
            if arg2_1 != 1:
                return
            # readfileblock
            n = self.read_four()
            self.read_n(n)
            
        else:
            raise NotImplementedError("Woops")

    def sub_4e2590(self):
        self.sub_7c17e0()
        # more
        v158 = self.sub_4e24f0() # is field 10
        for i in range(v158):
            # call field 14 i.e. sub_4e2310
            self.sub_4e2310()
        pass
        # TODO see what happens if arg4 not 0
        

    def sub_45b9e0(self):
        self.readExpectedTag(0x3352)
        v_c = self.read_four()
        sz = self.read_four()
        data = self.read_n(sz)
        if b'R3SG' not in data:
            raise ValueError("R3SG check error")
        self.read_one()

    def sub_73a400_some_sel_mgr(self):
        self.readExpectedTag(0x4d53)
        v20 = self.read_four()
        if v20 >= 1:
            v14 = self.read_four()
            for i in range(v14):
                self.read_four()
                self.read_four()
        else:
            raise NotImplementedError("v20 was 5")
        if v20 < 1:
            raise NotImplementedError("v20 was 5")
        if v20 < 2:
            raise NotImplementedError("v20 was 5")
        if v20 < 4:
            raise NotImplementedError("v20 was 5")
        if v20 < 5:
            raise NotImplementedError("v20 was 5")
        a8 = self.read_four()
        if a8 != 0xa:
            raise NotImplementedError("Always hoped it was 0xa")

        for i in range(a8):
            newArrSz = self.read_four()
            for j in range(newArrSz):
                self.read_four()
        
    def sub_6cd5a0(self):
        if self.fc >= 0x18:
            self.read_one()
    def sub_6cd7b0(self):
        self.read_one()

    def read_trigger(self):
        v120 = self.read_four()
        if v120 != 0:
            f_30 = self.read_four()
            if v120 > 1:
                a1_38 = self.read_four()
            if v120 > 2:
                f_34 = self.read_four()
        raise NotImplementedError("We did not finish this :(. Got bored and my test map had none")
            
    def read_trigger_group(self):

        v114 = self.read_four()
        if v114 < 0:
            raise ValueError("Bad 114")
        a1_0 = self.read_four()


        n = self.read_four()
        data = self.read_n(n)
        v110 = self.read_four()
        for i in range(v110):
            self.read_four()

    def sub_7a0880(self):

        self.readExpectedTag(0x5254)
        v18 = self.read_four()
        if v18 <= 3:
            raise ValueError("Idk looks bad")
        a1_0 = self.read_four()
        if v18 > 4:
            a1_4 = self.read_four()
        if v18 > 6:
            a1_8 = self.read_four()
        trigger_count = self.read_four()
        for i in range(trigger_count):
            self.read_trigger()
        if v18 > 5:
            trigger_group_count = self.read_four()
            for i in range(trigger_group_count):
                self.read_trigger_group()


    def sub_7f0fa0(self): # reads a bunch of proto unit names
        self.readExpectedTag(0x5450)
        v418 = self.read_four()
        v_40c = self.read_four()
        for i in range(v_40c):
            sz = self.read_four()
            data = self.read_n(sz)
            
    def sub_988490(self): #reads stuff like LogicalTypeHouses\x00
        self.readExpectedTag(0x4d54)
        v418 = self.read_four()
        v40_c = self.read_four()
        for i in range(v40_c):
            sz = self.read_four()
            data = self.read_n(sz)
    
    def command_manager_readStuff(self):
        self.readExpectedTag(0x324d)
        f_4 = self.read_four()
        v_8 = self.read_four()
        for i in range(v_8):
            data = self.read_one()
            if data != 0:
                v_10 = self.read_four() #cmd_type
                cmd = Commands.Command.get_command(v_10)
                cmd.read(self)

        # There might be some if here. I'm ignoring it.
        v_8 = self.read_four()
        for i in range(v_8):
            data = self.read_one()
            if data != 0:
                v_10 = self.read_four() #cmd_type
                cmd = Commands.Command.get_command(v_10)
                cmd.read(self)
        a_8 = self.read_four()
        if a_8 == 0x10:
            v_10 = self.read_four()
            if v_10 == 0xa:
                for i in range(a_8):
                    for j in range(v_10):
                        v_18 = self.read_four()
                        for k in range(v_18):
                            self.read_four()
                        self.read_four()
            
    def sub_5986b0(self, tag):
        x = self.read_2bytechecked_and4bytes(tag)
        n = self.read_four()
        data = self.read_n(n)
    def sub_5986f0(self, tag):
        x = self.read_2bytechecked_and4bytes(tag)
        n = self.read_four()
        data = self.read_n(4 * n)

    def sub_91c7b0(self):
        self.readExpectedTag(0x5454)
        v44c = self.read_four()
        v434 = self.read_four()
        for i in range(v434):
            n = self.read_four()
            self.read_n(n)
            
            v42c = self.read_four()
            for i in range(v42c):
                n = self.read_four()
                self.read_n(n)
    def sub_91cb50(self):
        self.readExpectedTag(0x4957)
        v24 = self.read_four()
        v18 = self.read_four()
        for i in range(v18):
            self.sub_598220()
    def sub_598220(self):
        v8 = self.read_four()
        n = self.read_four()
        self.read_n(n)

    def sub_7ea7a0(self):
        self.readExpectedTag(0x5451)
        v10 = self.read_four()
        a2 = self.read_four()
        for i in range(a2):
            vc = self.read_four()
            v8 = self.read_four()

    def bterrain_readStuff(self):
        self.readExpectedTag(0x3354)
        v1c = self.read_four()
        self.sub_91c7b0()
        f_8 = self.read_four()
        f_c = self.read_four()
        f_10 = f_8 + 1
        f_14 = f_c + 1
        f_18 = self.read_four()
        f_24 = self.read_four()

        self.sub_5986b0(0x5454)
        self.sub_5986b0(0x5354)

        if v1c <= 0:
            raise NotImplementedError("V1c small")
        self.sub_5986b0(0x4f54)
        self.sub_5986f0(0x4357)
        if v1c <= 2:
            self.sub_5986b0(0x5457)
            self.sub_5986b0(0x5357)
            raise NotImplementedError("Needs test")
        else:
            self.sub_91cb50()
            self.sub_5986b0(0x5457)
        for i in range(f_10):
            for j in range(f_14):
                self.read_four()
        for i in range(f_10):
            for j in range(f_14):
                self.read_four()
        self.sub_5986f0(0x544d)
        f_88 = self.read_four()
        if v1c == 4:
            self.sub_5986b0(0x5a54)
        if v1c >= 6:
            self.sub_7ea7a0()
    def read_slg(self):
        raise NotImplementedError("SLG")
        self.readExpectedTag(0x374e)

    def sub_6dd6b0(self):
        pass#TODO
    def bplayer_read_some_svx(self):
        self.readExpectedTag(0x5042)
        v1c = self.read_four()
        playerId = self.read_four()

        if v1c >= 0x26:
            n = self.read_four()
            data = self.read_n(2 * n)
            if v1c >= 0x39:
                f_10 = self.read_four()
        else:
            raise NotImplementedError(" I am lazy")
        if v1c >= 0x4d:
            f_620 = self.read_one()
            if v1c >= 0x4e:
                v24 = self.read_four()
                for i in range(v24):
                    v30 = self.read_four()

        playerTypeFlags = self.read_one()
        if v1c >= 1:
            f_18 = self.read_four()
        culture = self.read_four()
        civ = self.read_four()
        age = self.read_four()
        if v1c < 6:
            v24 = self.read_four()
            v24 = self.read_four()
            v24 = self.read_four()
        pop = self.read_four()
        pop_cap = self.read_four()
        f_3c = self.read_four()
        if v1c >= 0x34:
            f_40 = self.read_four()
        if v1c < 0x24:
            raise NotImplementedError("0069d442")
        colors = self.read_four()
        f_7c = self.read_four()
        f_80 = self.read_four()
        numSlgs = self.read_four()
        # last known good
        for i in range(numSlgs):
            self.read_slg()
        if v1c < 0x2c:
            raise NotImplementedError("0069d650")
        v24 = self.read_four()

        for i in range(v24):
            v18 = self.read_four()
            n = self.read_four()
            self.read_n(4 * n)

        #0069d6df
        v18 = min(self.read_four(), 0x10)
        print(v18)
        for i in range(v18):
            rel_stuff = self.read_four()
        
        score = self.read_four()
        teamScore = self.read_four()

        self.sub_6dd6b0()


        print(hex(self.seek), hex(v1c))

        print(culture, civ, CivManager(True).gods[civ])
    def player_read_some_svx(self):
        self.bplayer_read_some_svx()

    def world_readStuff(self):
        self.readExpectedTag(0x314a)
        v224 = self.read_four_s()
        if v224 < 0x34:
            raise ValueError("v224 < 0x34! wow!")
        # World::readStuff_likeCommandsActions() 
        self.skip(1210)

        if v224 >= 0x67:
            n = self.read_four()
            self.read_n(2*n)
        if v224 < 0x2f:
            self.readExpectedTag(0x544d)
        self.sub_7f0fa0()
        if v224 >= 0x15:
            self.sub_988490()
        if v224 >= 0x16:
            self.sub_988490()
        if v224 >= 0x2c:
            self.sub_988490()
        if v224 < 0x14:
            raise ValueError("< 14")
        self.command_manager_readStuff()
        v_249 = self.read_one()
        if v_249 == 1:
            if v224 < 0:
                raise ValueError("Negative")
            v230 = self.read_four()
            if v230 != 1:
                raise ValueError("Not one")
        print(" Seek pre terrain " + hex(self.seek))
        self.bterrain_readStuff()
        if v224 < 0x2b:
            raise ValueError("v224 < 2b! wow!")
        f_3fc = self.read_four()
        f_400 = self.read_four() 
        v234 = self.read_four()
        numPlayers = v234
        print(numPlayers)
        for i in range(numPlayers):
            v229 = self.read_one()
            if v229 != 0:
                self.player_read_some_svx()
        #0x67d664
        

    def parse_svx(self):
        print("Parsing svx")
        # self.read_two()
        # self.skip(6)
        self.fc = self.sub_7c16a0() # fc is eax_11 is v18
        # Taking arg3 == 0:
        if self.fc >= 2:
            self.sub_4e2590()
        #stuff if arg3 is not 0
        
        if self.fc < 0x16:
            raise NotImplementedError("We had 65")
        gs3 = self.read_one()
        if gs3 != 0:
            raise NotImplementedError("Has been zero")

        self.skip(6 * 10)

        self.sub_45b9e0() # is field_188
        if self.fc < 0x13:
            raise NotImplementedError("Sorry, we had 65")
        self.sub_73a400_some_sel_mgr()

        if self.fc >= 0x33:
            data_bc95d8 = self.read_four()
        else:
            data_bc95d8 = 0x31
        self.sub_6cd5a0()
        if self.fc >= 0xe:
            self.sub_6cd7b0()
        else:
            raise NotImplementedError("65")
        if self.fc > 5:
            self.sub_7a0880()
        
        self.world_readStuff()
        print(hex(self.seek))

        # I was looking at 0x665885 (field_8 call of savedgamething)

    ### END SVX



    def read_four(self):
        data = struct.unpack("<I", self.decomp[self.seek:self.seek+4])[0]
        self.seek += 4
        return data
    def read_float(self):
        data = struct.unpack("f", self.decomp[self.seek:self.seek+4])[0]
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
        if loadFlags & LOAD_FLAGS_COMMANDS_FEW:
            return self.read_one()
        if loadFlags & LOAD_FLAGS_COMMANDS_MANY == 0:
            return 0
        return self.read_four()

    def get_command(self, loadFlags):
        test = self.read_one()
        if test != 0:
            cmd_type = self.read_four()
            cmd = Commands.Command.get_command(cmd_type)
            cmd.read(self)
            return cmd
        return None

    def get_sync(self, loadFlags):
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
                decider = self.read_one()
                if decider != 0:
                    self.read_sync_update()
        else:
            if self.field_8 >= 2:
                return
            raise NotImplementedError("Field 8 weird")

    def read_sync_update(self):
        numSyncDatas = self.read_four()
        for i in range(numSyncDatas):
            first = self.read_one()
            self.read_one()
            self.read_two() #todo this was bugged i need to check
            if first & 0xf != 0x5:
                self.read_four()
            self.read_four()
            self.read_four()
        ar = self.read_four()

        for i in range(ar):
            sync_data = self.read_four()
    
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
        # print(f"Reading file of size {totalSize}")
        blockSize = self.read_four()
        if blockSize == 0:
            raise ValueError("Zero block size")
        return self.read_section(totalSize, blockSize)

class Player:
    def __init__(self, civ, team, idx, civ_mgr, isObserver=False, name=""):
        self.civ = civ
        self.team = team
        self.idx = idx
        self.name = name
        self.isResigned = False
        self.isObserver = isObserver
        self.civ_mgr = civ_mgr

    def setName(self, name):
        self.name = name

    def resign(self, resignTime):
        self.resignTime = resignTime
        self.isResigned = True

    def __str__(self):
        return self.name + "(" + self.get_civ_str() + ")"

    def __repr__(self):
        return self.__str__()

    def get_civ_str(self):
        return self.civ_mgr.get_god(self.civ)

class Team:
    def __init__(self, name, id):
        self.players = []
        self.name = name.decode("utf-8")
        self.id = id

    def addPlayer(self, player):
        self.players.append(player)

    def is_lost(self):
        for player in self.players:
            if not player.isResigned:
                return False
        return True

    def __str__(self):
        prepend = ""
        if self.is_observing_team():
            prepend = "Observing "
        return prepend + self.name  + " - " + str(self.players)
    
    def is_observing_team(self):
        for player in self.players:
            if not player.isObserver:
                return False
        return True 
    
    def has_player(self, player_name):
        for player in self.players:
            if player.name == player_name:
                return True
        return False

    def get_player(self, player_name):
        for player in self.players:
            if player.name == player_name:
                return player
        return None


class Update:
    def __init__(self, num, commands, selectedUnits, time):
        self.commands = commands
        self.selectedUnits = selectedUnits
        self.time = time
        self.num = num

    def set_num(self, num):
        self.num = num

class Rec:
    def __init__(self, filepath):
        self.players = []
        self.updates = []
        self.teams = []
        self.has_comp = False
        self.filepath = filepath

        # Create our RcxReader
        self.reader = RcxReader(filepath)
        self.is_ee = self.reader.is_ee
        self.civ_mgr = CivManager(self.is_ee)
        
        
    def parse_update(self, updateNum):
        selectedUnits = []
        commands = []

        loadFlags = self.reader.read_one()

        self.reader.read_camera(loadFlags)

        upTime = self.reader.get_update_time(loadFlags)
        
        # Read the commands
        numCommands = self.reader.read_num_commands(loadFlags)
        commands = [None] * numCommands
        for i in range(numCommands):
            commands[i] = self.reader.get_command(loadFlags)
            cmd = commands[i]
            if type(cmd) == Commands.PlayerDisconnectCommand:
                pass
            if type(cmd) == Commands.PlayerDisconnectCommand:
                # print(cmd, cmd.playerId, cmd.ac, self.players)
                # print(self.controlledPlayer)
                # print(self.xml)
                # print(self.players[cmd.playerId])
                # print(self.controlledPlayer)
                if cmd.playerId == self.controlledPlayer:
                    return Update(updateNum, commands, selectedUnits, upTime), False

        # Read the selected units
        if loadFlags & LOAD_FLAGS_SELECTED_UNITS:
            numUnits = self.reader.read_one()
            selectedUnits = [0] * numUnits
            for i in range(numUnits):
                selectedUnits[i] = self.reader.read_four()
        
        
        # Looks like this is players affected. Not 100% sure, but it seems to fix obs stuff
        playerAffCount = self.reader.read_one()
        for i in range(playerAffCount):
            pl = self.reader.read_one()
            
        # byte read from header field_4c

        # Read sync info
        self.reader.update = updateNum
        self.reader.get_sync(loadFlags)

        if self.reader.field_8 < 1:
            # self.validate_read()
            pass
        return Update(updateNum, commands, selectedUnits, upTime), True
    
    def parse_header(self):
        if self.reader.f_54:
            raise NotImplementedError("Game does not start from beginning")
        
        # read game settings (lastGameSettings.xml)
        lastGameSettingsXml = self.reader.read_file()
        
        self.xml = lastGameSettingsXml.decode("utf-16")

        # read map script (recordGameRandomMap.xs)
        self.recordGameMap = self.reader.read_file()
        
        # Read info about the players (civ, team)
        numPlayers = self.reader.read_four()

        # if not self.is_ee:
        #     if numPlayers > 4:
        #         raise NotImplementedError("Voobly games with > 3 players not supported. The 2 obs things is why")

        for i in range(numPlayers):
            playerCiv = self.reader.read_four_s()
            playerTeam = self.reader.read_four_s()
            
            curPlayer = Player(playerCiv, playerTeam, i-1, self.civ_mgr, isObserver=playerTeam==-1)
            self.players.append(curPlayer)
        # print(numPlayers, playerCiv, playerTeam)
            
        # Match players we just read with players from Xml File
        # This lets us find attributes such as the player name
        num_observers = 0
        root = ET.fromstring(self.xml)
        self.map = root.findall("Filename")[0].text

        # Read controlled player
        self.controlledPlayer = int(root.findall("CurrentPlayer")[0].text)
        # Iterate through all players and get their civ
        for player_ele in root.findall("Player"):
            if 'ClientIndex' in player_ele.attrib:
                idx = player_ele.attrib['ClientIndex']
            else:
                idx = player_ele.attrib['ClientID']
            idx = int(idx)+1

            player_type = int(player_ele.find("Type").text)
            
            player = self.players[idx-num_observers]
            name = player_ele.find("Name").text
            if idx == self.controlledPlayer:
                self.controlledPlayer -= num_observers
            if player_type == PLAYER_TYPE_COMP:
                self.has_comp = True
            if player_type == PLAYER_TYPE_HUMAN or PLAYER_TYPE_COMP: ## This could pollute stats if not accounted for
                if name is not None:
                    player.setName(name)
            elif player_type == PLAYER_TYPE_OBS:
                num_observers += 1

        
        
        # Skip 1 + 4 + 4 + 4 bytes found after the civ,team info
        self.reader.skip(9)
        self.reader.skip(4)

        # Read the difficulty, team nums
        self.difficulty = self.reader.read_four()
        maybeTeamNums = self.reader.read_four() 
        
        # I don't currently know if teamIds can descend. This lets us check for that
        lastTeamId = START_LAST_TEAM_ID
        
        # For every player read some more info about them
        for i in range(maybeTeamNums):
            read_player = self.reader.read_one()
            if read_player == 0:
                continue
            self.reader.skip(4)
            
            teamId = self.reader.read_four()
            sz = self.reader.read_four()
            teamDesc = self.reader.read_n(sz)
            if not self.is_ee:
                if lastTeamId != START_LAST_TEAM_ID:
                    if teamId < lastTeamId:
                        raise NotImplementedError("Descending team ids")

            if teamId-1 < len(self.teams):
                self.teams[teamId-1].set_name(teamDesc)
            else:
                self.teams.append(Team(teamDesc, teamId))

            newNum = self.reader.read_four() #might be color stuff, can't remember
            for i in range(newNum):
                data = self.reader.read_four()
            lastTeamId = teamId
        

            
        # We now read more info about the players.
        # Not exactly sure what all this is
        # In there is civ, culture, and maybe the default stance
        # Also in there is the starting relation with other players
        # Some color info too
        alsoNumPlayers = self.reader.read_four()
        if alsoNumPlayers != numPlayers:
            raise ValueError("ERROR. alsoNumPlayers doesn't match")

        players2 = []
        for i in range(alsoNumPlayers):
            tester = self.reader.read_one()
            if tester == 0:
                continue
            check_3f = self.reader.read_four_s()
            god_flags_idk_dude = self.reader.read_one()
            god_flags_idk_dude2 = self.reader.read_one()
            maybe_stance = self.reader.read_four()


            # sub_512b30

            player_name_len = self.reader.read_four()
            player_name_2 = self.reader.read_n(2*player_name_len)
            field_10 = self.reader.read_four()
            type_flags = self.reader.read_one()

            culture = self.reader.read_four()
            civ = self.reader.read_four()
            field_18 = self.reader.read_four_s() #seems to be team again
            players2.append(Player(civ, field_18, i, self.civ_mgr, isObserver=field_18==-1, name=player_name_2.decode("utf-16")))
            lastTeamId = field_18
            field_4b4 = self.reader.read_four()
            field_4b8 = self.reader.read_four()
            if check_3f >= 0x3f:
                test2 = self.reader.read_four_s()
                if test2 > 0x10:
                    print("PL NUM ERR")
                    return
                
                if test2 > 0:
                    for j in range(test2):
                        rel = self.reader.read_four()
                        # if i == 3:
                        #     print(rel)
            colors = self.reader.read_four()
            # if i == 3:
            #     print(i, tester, check_3f, god_flags_idk_dude, god_flags_idk_dude2, maybe_stance)
            #     print(player_name_2.decode("utf-16"))
            #     print(field_10, type_flags, culture, civ)
            #     print(field_18, field_4b4, field_4b8, colors)
            #     print(test2)
        self.players = players2
        
        # Add players to their team

        for player in self.players:
                #TODO
            # Check what's going on here. I think this is correct, but some of the above code may be wrong
            # I still am not sure exactly how the game handles observers
            # Maybe easiest thing to do is skip processing players
            if player.team == -1 or player.team==0: 
                continue
            # voobly multiple observer stuff
            if not self.is_ee:
                if player.team == lastTeamId and num_observers >= 1 and maybeTeamNums > 3:
                    player.isObserver = True
            if player.civ != self.civ_mgr.get_nature_idx():
                if player.name != "":
                    self.teams[player.team-1].addPlayer(player)
    

    def parse(self, print_progress=False):
        self.parse_header()
        
        # Now we parse all the updates
        time = 0
        for updateNum in range(1,0x1000001):
            pre = self.reader.seek
            try:
                update, keep_read = self.parse_update(updateNum)
            except Exception as e:
                print("At offset " + hex(pre) +" and update " + hex(updateNum) + " we had an error.")
                raise e
            self.updates.append(update)
            if updateNum % 20000 == 0:
                if print_progress:
                    print("Parsing progress: {:.2f}%".format(self.reader.seek * 100 / len(self.reader.decomp)))
            if len(self.reader.decomp) == self.reader.seek:
                break
            if not keep_read:
                break
            # print(hex(self.reader.seek), hex(updateNum), self.reader.seek-pre, hex(len(self.reader.decomp)))
            time += update.time
            # print(self.game_time_formatted(time))
            # print(self.players)
        if print_progress:
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
        print(self.map)
        for team in self.teams:
            print(team)

    def print_winner(self):
        winningTeam = self.get_winning_team()
        if winningTeam is not None:
            print(winningTeam.name + " has won")
        else:
            print("Game not finished")

    def __repr__(self):
        return self.get_display_string()

    def get_display_string(self):
        teams = [[] for i in range(len(self.players))]
        for player in self.players:
            if player.team <= 0: #handles obs i think
                continue
            else:
                team = teams[player.team]
                team.append(player)
        
        ret = os.path.basename(self.filepath) + "\n\t" + self.map +"\n"
        for team in teams:
            if len(team) > 0:
                ret += ("\tTeam " + str(team[0].team)+": ")
                for player in team:
                    ret+= (str(player) + " ")
                ret += "\n"

        return ret
    
    def game_time_milliseconds(self):
        time = 0
        for update in self.updates:
            time += update.time
        return time

    def print_checked(self, input, print_info):
        if print_info:
            print(input)

    def analyze_updates(self, print_info=False):
        ttdatabase = TechTreeDatabase()
        pudatabase = ProtoUnitDatabase()
        time = 0
        i = 0
        for update in self.updates:
            commands = update.commands
            for command in commands:
                # if command.resigningPlayerId == 3:
                #     print(command)
                if type(command) == Commands.ResignCommand:
                    self.players[command.resigningPlayerId].resign(time)
                    # if not self.players[command.resigningPlayerId].isObserver:
                    self.print_checked(str(self.players[command.resigningPlayerId]) + " has resigned", print_info)
                elif type(command) == Commands.ResearchCommand:
                    self.print_checked(str(self.players[command.playerId]) + " clicked " + ttdatabase.get_tech(command.techId)
                     + " at " + self.game_time_formatted(time), print_info)
                elif type(command) == Commands.PlayerDisconnectCommand:
                    self.print_checked(str(self.players[command.playerId]) + " has disconnected", print_info)
                elif type(command) == Commands.BuildCommand:
                    if False:
                        self.print_checked(str(self.players[command.playerId]) + " has built " + pudatabase.get_displayname(command.protoUnitId)
                        + " at " + self.game_time_formatted(time), print_info)
                elif type(command) == Commands.TrainCommand:
                    if False:
                        self.print_checked(str(self.players[command.playerId]) + " tried training " + pudatabase.get_displayname(command.mProtoUnitId)
                        + " at " + self.game_time_formatted(time), print_info)
                # elif type(command) == Commands.WorkCommand:
                #     print(command.playerId)
                #     print(str(command.mUnitId))
                #     print(str(command.mRange))
                #     print(str(command.mTerrainPoint))

                #     print(str(command.mRecipients))
                #     print()

                else:
                    pass
                    # if time > 930000 and time < 945000:
                    #     if command.playerId == 2:
                    #         print(command, self.game_time_formatted(time), self.players[command.playerId])
                    #         if type(command) == Commands.BuildCommand:
                    #             print(pudatabase.get_displayname(command.protoUnitId))
            time += update.time
            i += 1

    def game_time_formatted(self, ms=None):
        if ms is None:
            ms = self.game_time_milliseconds()
        seconds = ms/1000
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins}:{secs:02}"


    def get_winning_team(self):
        winningTeam = None
        winners = 0
        for team in self.teams:
            if team.is_observing_team():
                continue
            if not team.is_lost():
                winningTeam = team
                winners += 1
        if winners == 1:
            return winningTeam
        return None
    
    def get_losing_teams(self):
        losingTeams = []
        for team in self.teams:
            if team.is_observing_team():
                continue
            if team.is_lost():
                losingTeams.append(team)
        return losingTeams
    
    def clear_data(self):
        self.reader.decomp = b""
    
    def recreate_data(self):
        seek = self.reader.seek
        self.reader = RcxReader(self.filepath)
        self.reader.seek = seek
            
def analyze_group(folderpath, is_ee=True):
    errors = {}
    god_wins = {}
    god_losses = {}
    folderpath += os.sep


    duplicate_test = {}
    for file in os.listdir(folderpath):
        if file.endswith(".rcx"):
            try:
                print(file)
                rec = Rec(folderpath + file)
                rec.parse()
                rec.analyze_updates()
                rec.display_by_teams()
                # rec.print_winner()
                
                winning_team = rec.get_winning_team()
                losing_teams = rec.get_losing_teams()
                if winning_team is None:
                    print("No winning team ")
                    continue
                if len(losing_teams) < 1:
                    print("No losing team")
                    continue
                if winning_team is not None:
                    for player in winning_team.players:
                        winning_civ = player.get_civ_str()
                        if winning_civ in god_wins:
                            god_wins[winning_civ] += 1
                        else:
                            god_wins[winning_civ] = 1
                    for losing_team in losing_teams:
                        for player in losing_team.players:
                            losing_civ = player.get_civ_str()
                            if losing_civ in god_losses:
                                god_losses[losing_civ] += 1
                            else:
                                god_losses[losing_civ] = 1
                
                # if str(winning_team) in duplicate_test:
                #     losers = duplicate_test[str(winning_team)]
                    
                #     for loser in losers:
                #         losing_team_str = loser[0]
                #         lose_file = loser[1]
                #         # print(str(losing_team), losing_team_str + " A ")
                #         if str(losing_team) == losing_team_str:
                #             print("Duplicate game: " + lose_file + " == " + file)
                #             continue
                #     losers.append([str(losing_team), file])
                # else:
                #     duplicate_test[str(winning_team)] = [[str(losing_team),file]]
                # print(str(winning_team), str(losing_team))
                    
                # print(winning_team,"beat", losing_team)
                # else:
                #     print("Error: " + file + " has no winner")
            except Exception as e:
                print(e, file + " was here")
                e = str(e)
                if e in errors:
                    abc = errors[e]
                    abc[0] += 1
                    abc[1].append(file)
                else:
                    errors[e] = [1, [file]] 
    all_gods = ["Zeus", "Poseidon", "Hades", "Isis", "Ra", "Set", "Odin", "Thor", "Loki", "Kronos", "Oranos", "Gaia", "Fu Xi", "Nu Wa", "Shennong"]
    for god in all_gods:
        wins = 0
        losses = 0
        if god in god_wins:
            wins = god_wins[god]
        if god in god_losses:
            losses = god_losses[god]
        total = wins + losses
        if total > 0:
            percent_wins = round(wins/total * 100)
            print(f"{god} won {percent_wins}% out of {total} games. They went {wins}-{losses}")
    print(errors)
    num_games = sum([god_wins[x] for x in ["Zeus", "Poseidon", "Hades", "Isis", "Ra", "Set", "Odin", "Thor", "Loki", "Kronos", "Oranos", "Gaia"]])
    num_games2 = sum([god_losses[x] for x in ["Zeus", "Poseidon", "Hades", "Isis", "Ra", "Set", "Odin", "Thor", "Loki", "Kronos", "Oranos", "Gaia"]])
    print(num_games2, num_games)

def parse_all_headers(base):
    recs = []
    import traceback
    for file in os.listdir(base):
        if file.endswith(".rcx"):
            try:
                rec = Rec(base + file)
                rec.parse_header()
                recs.append(rec)
                rec.clear_data()
                # f.write(file + " worked\n")
            except Exception as e:
                print(file + "  " + str(e))
                # f.write(file + " " + str(e))
                # f.write(traceback.format_exc())
    return recs

def filter_by_player(recs, player_name, god="*", opposing_player_name="*", opposing_god="*"):
    ret_recs = []
    for rec in recs:
        found_player = False
        for team in rec.teams:
            if team.is_observing_team():
                continue
            if team.has_player(player_name):
                if god == "*" or rec.civ_mgr.get_god(team.get_player(player_name).civ) == god:
                    found_player = True


        if found_player:
            found_opponent = False 
            for team in rec.teams:
                if team.is_observing_team() or team.has_player(player_name):
                    continue
                # Check opposing player
                if opposing_player_name=="*" or team.has_player(opposing_player_name):
                    for player in team.players:
                        # Check opposing god
                        if opposing_god == "*" or rec.civ_mgr.get_god(player.civ) == opposing_god:
                            found_opponent = True
                        

            if found_opponent:
                ret_recs.append(rec)
    return ret_recs

def filter_by_1v1s(recs):
    ret_recs =[]
    for rec in recs:
        team_count = 0
        bad_player_count = False
        for team in rec.teams:
            if not team.is_observing_team():
                team_count += 1
                if len(team.players) != 1:
                    bad_player_count = True
        if team_count == 2 and not bad_player_count:
            ret_recs.append(rec) 
    return ret_recs

def filter_by_map(recs, map="*"):
    ret_recs = []
    for rec in recs:
        if map=="*" or map == rec.map:
            ret_recs.append(rec)
    return ret_recs

def write_headers(recs, file=None):
    if file is not None:
        with open(file, "w") as f:
            for rec in recs:
                f.write(rec.get_display_string())
    else:
        for rec in recs:
            print(rec.get_display_string(),end="")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs="?")
    args = parser.parse_args()
    # analyze_group("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame")
    if args.filename is not None:
        rec = Rec(args.filename)
        rec.parse(print_progress=True)
        rec.analyze_updates(print_info=True)
        rec.display_by_teams()
        rec.print_winner()
        print("Game time " + rec.game_time_formatted())
    else:
        # parse_many_recs("/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/")
        savegame_path = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Age of Mythology/savegame/"
        if not os.path.exists(savegame_path):
            savegame_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Age of Mythology\\savegame\\"
        recs = parse_all_headers(savegame_path)
        recs = filter_by_1v1s(recs)
        recs = filter_by_player(recs,"Kido", god="Set", opposing_god="*")
        recs = filter_by_map(recs, "*")
        write_headers(recs, "recs.txt")

    # # rec = Rec("3_ppl_1v1_obs_is_titled_as_player_in_program.rcx")
    # # rec = Rec()
    # rec = Rec("rcxs/nube1978_cheat_obs.rcx", is_ee=False)
    # # rec = Rec(AOM_PATH+os.sep+"savegame"+os.sep+"BuyMerge_vs_White.rcx")
    # analyze_group("/mnt/c/Users/stnevans/Downloads/megardm", is_ee=False)
    # analyze_group("/mnt/c/Users/stnevans/Documents/My Games/Age of Mythology/Savegame/megardm")
    # analyze_group("/mnt/c/Program Files (x86)/Microsoft Games/Age of Mythology/savegame/megardm", is_ee=False)

    # analyze_group(AOM_PATH+os.sep+"savegame/")
    
    

if __name__ == '__main__':
    main()