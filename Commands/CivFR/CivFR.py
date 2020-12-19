import random
from discord import AllowedMentions

from util.exception import InvalidArgs, Forbidden
from .constant import CIVFR_GUILD_ID
from .utils import is_civfr_guild_or_mp

class CmdCivGeneralFR:
    async def cmd_coinflip(self, channel, *_, **__):
        await channel.send("Pile" if random.randint(0, 1) else "Face")

    async def cmd_dindon(self, *args, channel, **_):
        if not is_civfr_guild_or_mp(channel):
            raise Forbidden("This commands is only aviable on CivFR")
        if not args:
            raise InvalidArgs("Command argument must be 'now' or 'xxhxx'")
        if args[0] == 'now':
            await channel.send("@here la partie va bientôt commencer. Veuillez vous connecter dans 'Salle d'attente' 🦃", allowed_mentions=AllowedMentions(everyone=True))

    async def cmd_debutant(self, *args, channel, **_):
        if not is_civfr_guild_or_mp(channel):
            raise Forbidden("This commands is only aviable on CivFR")
        await channel.send("https://www.youtube.com/watch?v=o2iiCC9nXEc")