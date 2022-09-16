class Command:
    #mRecipients seems to be unitid of units that are processed by command


    def __init__(self):
        self.mRecipients = []

    def read(self,reader):
        self.num = reader.read_one()
        self.playerId = reader.read_four()

        self.field_28 = reader.read_four()

        self.mAIID = reader.read_four()
        
        self.field_30 = reader.read_four()

        self.field_34_len = reader.read_four()
        for i in range(self.field_34_len):
            reader.read_four()

        self.field_48 = reader.read_four()

        self.mRecipientsLen = reader.read_four()
        for i in range(self.mRecipientsLen):
            self.mRecipients.append(reader.read_four())
        
        self.waypointsLen = reader.read_four()
        for i in range(self.waypointsLen):
            reader.read_four()
            reader.read_four()
            reader.read_four()

        # read mFlags  
        mFlagsSize = reader.read_four()
        reader.read_n(mFlagsSize)

        self.field_8c = reader.read_four()
        self.field_90 = reader.read_four()
        self.field_94 = reader.read_four()
        self.mUrgencyCount = reader.read_one()
        self.mEventId = reader.read_four()
        self.mPlanId = reader.read_four()

    def get_command(commandNum):
        map = {0: WorkCommand, 1: ResearchCommand, 2 : TrainCommand, 3: BuildCommand, 
               4: SetGatherPointCommand, 5: None, 6: CreateUnitCommand, 7: DeleteUnitCommand,
               8: None, 9: AddResourceCommand, 0xa: StopCommand, 0xb: None, 0xc: None,
               0xd: None, 0xe: None, 0xf: PauseCommand, 0x10: SpecialPowerCommand, 
               0x11: MarketCommand, 0x12: EjectCommand, 0x13: None,
               0x14: ResignCommand, 0x15: None, 0x16: EnterCommand, 0x17: TributeCommand,
               0x18: None, 0x19: None, 0x1a: None, 0x1b: None, 0x1c: TransformCommand,
               0x1d: None, 0x1e: None, 0x1f: None, 0x20: None, 0x21: StanceCommand,
               0x22: None, 0x23: None, 0x24: None, 0x25: None, 0x26: None, 0x27: None,
               0x28: None, 0x29: None, 0x2a: TownBellCommand, 0x2b: ExploreCommand,
               0x2c: None, 0x2d: AdjustArmyCommand, 0x2e: RepairCommand, 0x2f: EmpowerCommand,
               0x30: None, 0x31: AiChatCommand, 0x32: PlayerDataCommand, 
               0x33: FormationCommand, 0x34: None, 0x35: UnbuildCommand, 0x36: AutoqueueCommand,
               0x37: PlayerAutoGatherModeCommand, 0x38: PlayerSpeedUpConstructionCommand, 0x39: PlayerDisconnectCommand}
        if commandNum not in map:
            print("Cannot find command in map. Probably wrong num")
            return None
        if map[commandNum] is None:
            print("Command " + hex(commandNum) + " not implemented")
            return None
        return map[commandNum]()
class PlayerSpeedUpConstructionCommand(Command):
    def __init__(self):
        super().__init__()
    
    def read(self, reader):
        super().read(reader)
class PlayerAutoGatherModeCommand(Command):
    def __init__(self):
        super().__init__()
    
    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()

class EmpowerCommand(Command):
    def __init__(self):
        super().__init__()
    
    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()

class EjectCommand(Command):
    def __init__(self):
        super().__init__()
    
    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()
    
class UnbuildCommand(Command):
    def __init__(self):
        super().__init__()
    
    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_posVector()
        self.d2 = reader.read_posVector()

class PauseCommand(Command): 
    def __init__(self):
        raise NotImplementedError("Check needed")

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_one()

class AddResourceCommand(Command): 
    def __init__(self):
        raise NotImplementedError("Check needed")
        
    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()
        self.d2 = reader.read_four()

class CreateUnitCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.protoId = reader.read_four()
        self.heading = reader.read_posVector()
        self.pos = reader.read_posVector()
        self.nameLen = reader.read_four()
        blkSize = reader.read_four()
        self.name = reader.read_n(self.nameLen)

class FormationCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.formation = reader.read_one()

class RepairCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()

class TownBellCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)

class PlayerDataCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        reader.read_four()

class MarketCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.res = reader.read_four()
        self.field_b0 = reader.read_four()
        self.amt = reader.read_four()
    
class TributeCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.res = reader.read_four()
        self.to = reader.read_four()
        self.amt = reader.read_four()
        self.field_b8 = reader.read_four()

class TransformCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        reader.read_four()
        reader.read_one()

class EnterCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()

class AdjustArmyCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)

        self.d1 = reader.read_one()
        self.d2 = reader.read_four()

class PlayerDisconnectCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        print("BEFORE = " + hex(reader.seek))
        self.playerId = reader.read_four()

        super().read(reader)

class SpecialPowerCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()
        self.d2 = reader.read_posVector()
        self.d3 = reader.read_posVector()
        self.d4 = reader.read_four()

class ResearchCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.techId = reader.read_four()
        self.field_b0 = reader.read_four()


class AiChatCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        reader.read_four()
        reader.read_four()
        reader.read_four()

        reader.read_four()
        reader.read_four()
        reader.read_four()
        reader.read_four()
        reader.read_posVector()

class DeleteUnitCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_one()

class ResignCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.resigningPlayerId = reader.read_four()
        self.d2 = reader.read_four() #maybe left in team
        self.d3 = reader.read_four() #maybe playerCount
        
class BuildCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()
        self.d2 = reader.read_posVector()

        self.d3 = reader.read_posVector()

        self.resId = reader.read_four()
        self.field_cc = reader.read_four()

class WorkCommand(Command):
    # Potentially a group of units (mRecipients) does work on a unit

    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.mUnitId = reader.read_four()

        self.mRange = reader.read_four()

        self.mTerrainPoint = reader.read_posVector()
    
class AutoqueueCommand(Command):
    def __init__(self):
        super().__init__()

class ExploreCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.some = reader.read_four()

class SetGatherPointCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.d1 = reader.read_four()
        self.d2 = reader.read_four()
        self.d3 = reader.read_four()

        self.d4 = reader.read_four()
        self.d5 = reader.read_four()

        
class StanceCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.probStance = reader.read_one()

class StopCommand(Command):
    def __init__(self):
        super().__init__()

class TrainCommand(Command):
    def __init__(self):
        super().__init__()

    def read(self, reader):
        super().read(reader)
        self.mProtoUnitId = reader.read_four()
        self.mAction = reader.read_four()
        self.mArmyId = reader.read_four()

