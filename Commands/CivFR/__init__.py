from .CivFR import CmdCivGeneralFR
from .DynamicDraft import CmdCivFRDDraft
from .FFATournament import CmdFFATournament
from .Draft import CmdCivDraft

class CmdCivFR(CmdCivGeneralFR, CmdCivFRDDraft, CmdCivDraft):
    pass