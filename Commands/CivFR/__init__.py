from .CivFR import CmdCivGeneralFR
from .DynamicDraft import CmdCivFRDDraft
from .FFATournament import CmdFFATournament
from .Draft import CmdCivDraft
from .Voting import CmdCivFRVoting
from .Level import CmdCivFRLevel
from .TeamerTool import CmdTeamerTools

class CmdCivFR(CmdCivGeneralFR, CmdCivFRDDraft, CmdCivDraft, CmdCivFRVoting, CmdCivFRLevel, CmdTeamerTools):
    pass