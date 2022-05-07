from .CivFR import CmdCivGeneralFR
from .DynamicDraft import CmdCivFRDDraft
from .FFATournament import CmdFFATournament
from .Draft import CmdCivDraft
from .Voting import CmdCivFRVoting
from .Level import CmdCivFRLevel
from .TeamerTool import CmdTeamerTools
from .Ranked.commands import CmdCivFRRanked
from .Ranked.Leaderboards import CmdLeaderboards

class CmdCivFR(CmdCivGeneralFR, CmdCivFRDDraft, CmdCivDraft, CmdCivFRVoting, CmdCivFRLevel, CmdTeamerTools,
               CmdCivFRRanked, CmdLeaderboards):
    pass