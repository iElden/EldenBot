from .CivFR import CmdCivGeneralFR
from .DynamicDraft import CmdCivFRDDraft
from .FFATournament import CmdFFATournament
from .Draft import CmdCivDraft
from .Voting import CmdCivFRVoting

class CmdCivFR(CmdCivGeneralFR, CmdCivFRDDraft, CmdCivDraft, CmdCivFRVoting):
    pass