import random

from util.exception import InvalidArgs
from .Leaders import leaders
from .DynamicDraft import get_draft

class CmdCivGeneralFR:
    async def cmd_draft(self, *args : str, channel, client, **_):
        if not args:
            raise InvalidArgs("Command should take at least one parameter")
        if not args[0].isdigit():
            raise InvalidArgs("1st Argument must be a integer (exemple: ``/draft 2``)")
        nb = int(args[0])
        drafts = get_draft(nb, *args[1:], client=client)

        result = []
        for i in range(nb):
            result.append(f"n°{i+1} | {', '.join(drafts[i])}")
        txt = ""
        for r in result:
            if len(txt) + len(r) >= 2000:
                await channel.send(txt)
                txt = r
            else:
                txt += '\n' + r
        await channel.send(txt)

    async def cmd_coinflip(self, channel):
        await channel.send("Pile" if random.randint(0, 1) else "Face")

