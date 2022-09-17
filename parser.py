
import struct
import zlib
import xml.etree.ElementTree as ET
import ntpath
import os
import sys

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

    def __init__(self, filepath, is_ee):
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
            for i in range(n):
                self.read_four()
            a120 = self.read_four()
            n = self.read_four()
            for i in range(n):
                self.read_four()
        v3b5 = self.read_one()
        f_54 = self.read_four()
        v3d0 = self.read_four()
        
        # World::readStuff_likeCommandsActions consumes 1210
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
            self.read_two()
            if first & 0xf != 0x5:
                self.read_four()
            self.read_four()
            self.read_four()
        ar = self.read_four()
        for i in range(ar):
            self.read_four()
    
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
    def __init__(self, civ, team, idx, civ_mgr, isObserver=False):
        self.civ = civ
        self.team = team
        self.idx = idx
        self.name = ""
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
        return self.name  + " - " + str(self.players)


class Update:
    def __init__(self, num, commands, selectedUnits, time):
        self.commands = commands
        self.selectedUnits = selectedUnits
        self.time = time
        self.num = num

    def set_num(self, num):
        self.num = num

class Rec:
    def __init__(self, filepath, is_ee=True):
        self.players = []
        self.updates = []
        self.teams = []

        self.filepath = filepath

        # Create our RcxReader
        self.reader = RcxReader(filepath, is_ee)
        self.civ_mgr = CivManager(is_ee)
        self.is_ee = is_ee
        
        
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
                if cmd.playerId == self.controlledPlayer:
                    return Update(updateNum, commands, selectedUnits, upTime), False


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
        return Update(updateNum, commands, selectedUnits, upTime), True
    
    def parse_header(self):
        # read game settings (lastGameSettings.xml)
        lastGameSettingsXml = self.reader.read_file()          
        self.xml = lastGameSettingsXml.decode("utf-16")

        # read map script (recordGameRandomMap.xs)
        self.recordGameMap = self.reader.read_file()
        
        # Read info about the players (civ, team)
        numPlayers = self.reader.read_four()
        for i in range(numPlayers):
            playerCiv = self.reader.read_four_s()
            playerTeam = self.reader.read_four_s()
            
            curPlayer = Player(playerCiv, playerTeam, i-1, self.civ_mgr)
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

        # Read controlled player
        self.controlledPlayer = int(root.findall("CurrentPlayer")[0].text)

        # Skip 1 + 4 + 4 + 4 bytes found after the civ,team info
        self.reader.skip(9)
        self.reader.skip(4)

        # Read the difficulty, team nums
        self.difficulty = self.reader.read_four()
        maybeTeamNums = self.reader.read_four()
        
        # For every player read some more info about them
        for i in range(maybeTeamNums):
            read_player = self.reader.read_one()
            if read_player == 0:
                continue
            self.reader.skip(4)
            
            teamId = self.reader.read_four()
            sz = self.reader.read_four()
            teamDesc = self.reader.read_n(sz)

            if teamId-1 < len(self.teams):
                self.teams[teamId-1].set_name(teamDesc)
            else:
                self.teams.append(Team(teamDesc, teamId))

            newNum = self.reader.read_four() #might be color stuff, can't remember
            for i in range(newNum):
                data = self.reader.read_four()
        
        # Add players to their team
        for player in self.players:
            #TODO
            # Check what's going on here. I think this is correct, but some of the above code may be wrong
            # I still am not sure exactly how the game handles observers
            if player.team == -1: 
                continue
            if player.civ != self.civ_mgr.get_nature_idx():
                if player.name != "":
                    self.teams[player.team-1].addPlayer(player)
            
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
            god_flags_idk_dude2 = self.reader.read_one()
            maybe_stance = self.reader.read_four()


            # sub_512b30

            some = self.reader.read_four()
            more = self.reader.read_n(2*some)

            field_10 = self.reader.read_four()
            type_flags = self.reader.read_one()

            culture = self.reader.read_four()
            civ = self.reader.read_four()

            field_18 = self.reader.read_four() #seems to be team again
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
            colors = self.reader.read_four()
    

    def parse(self, print_progress=False):
        self.parse_header()

        # Now we parse all the updates
        time = 0
        for updateNum in range(1,0x1000000):
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
        for team in self.teams:
            print(team)

    def print_winner(self):
        winningTeam = self.get_winning_team()
        if winningTeam is not None:
            print(winningTeam.name + " has won")
        else:
            print("Game not finished")


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
    
    def game_time_milliseconds(self):
        time = 0
        for update in self.updates:
            time += update.time
        return time

    def print_checked(self, input, print_info):
        if print_info:
            print(input)

    def analyze_updates(self, print_info=False):
        database = TechTreeDatabase()
        time = 0
        for update in self.updates:
            commands = update.commands
            for command in commands:
                if type(command) == Commands.ResignCommand:
                    self.players[command.resigningPlayerId].resign(time)
                    self.print_checked(str(self.players[command.resigningPlayerId]) + " has resigned", print_info)
                elif type(command) == Commands.ResearchCommand:
                    self.print_checked(str(self.players[command.playerId]) + " clicked " + database.get_tech(command.techId) + " at " + self.game_time_formatted(time), print_info)
                elif type(command) == Commands.PlayerDisconnectCommand:
                    self.print_checked(str(self.players[command.playerId]) + " has disconnected", print_info)
                    
                # elif type(command) == Commands.WorkCommand:
                #     print(command.playerId)
                #     print(str(command.mUnitId))
                #     print(str(command.mRange))
                #     print(str(command.mTerrainPoint))

                #     print(str(command.mRecipients))
                #     print()
                else:
                    pass
                    # print(command)
            time += update.time

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
            if not team.is_lost():
                winningTeam = team
                winners += 1
        if winners == 1:
            return winningTeam
        return None
    
    def get_losing_teams(self):
        losingTeams = []
        for team in self.teams:
            if team.is_lost():
                losingTeams.append(team)
        return losingTeams
            
def analyze_group(folderpath):
    god_wins = {}
    god_losses = {}
    for file in os.listdir(folderpath):
        if file.endswith(".rcx"):
            try:
                print(file)
                rec = Rec(folderpath + file, is_ee=True)
                rec.parse()
                rec.analyze_updates()
                # rec.display_by_teams()
                # rec.print_winner()
                winning_team = rec.get_winning_team()
                if winning_team is not None:
                    for player in winning_team.players:
                        winning_civ = player.get_civ_str()
                        if winning_civ in god_wins:
                            god_wins[winning_civ] += 1
                        else:
                            god_wins[winning_civ] = 1
                    for losing_team in rec.get_losing_teams():
                        for player in losing_team.players:
                            losing_civ = player.get_civ_str()
                        if losing_civ in god_losses:
                            god_losses[losing_civ] += 1
                        else:
                            god_losses[losing_civ] = 1
                # else:
                #     print("Error: " + file + " has no winner")
            except Exception as e:
                print(e, file)
                # raise e
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
            percent_wins = int(wins/total * 100)
            print(f"{god} won {percent_wins}% out of {total} games")
def main():
    
    # rec = Rec("/mnt/c/Users/stnevans/Documents/My Games/Age of Mythology/Savegame/" + "Recorded Game 4.rcx", is_ee=False)
    
    rec = Rec(AOM_PATH+os.sep+"savegame"+os.sep+"Replay v2.8 @2021.08.19 214544.rcx") # this is the player disconnect at end
    #Replay v2.8 @2021.08.17 222439.rcx
    # Replay v2.8 @2021.08.18 162542.rcx
    # Replay v2.8 @2022.01.20 183827.rcx
    #observer stuff Replay v2.8 @2021.08.19 214544.rcx
    # rec = Rec(AOM_PATH+os.sep+"savegame"+os.sep+"Replay v2.8 @2020.10.20 014718.rcx") # this is the player disconnect at end
    
    rec.parse(print_progress=True)
    rec.analyze_updates(print_info=True)
    rec.display_by_teams()
    rec.print_winner()
    # print("Game time " + rec.game_time_formatted())
    # analyze_group("/mnt/c/Users/stnevans/Documents/My Games/Age of Mythology/Savegame/")
    # analyze_group(AOM_PATH+os.sep+"test/")

if __name__ == '__main__':
    main()