import random

from util.exception import InvalidArgs
from .Leaders import leaders
from .DynamicDraft import get_draft

class CmdCivGeneralFR:
    async def cmd_coinflip(self, channel, *_, **__):
        await channel.send("Pile" if random.randint(0, 1) else "Face")

