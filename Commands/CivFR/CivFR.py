import random
import nextcord
from nextcord import AllowedMentions

from util.exception import InvalidArgs, Forbidden
from .constant import CIVFR_GUILD_ID
from .utils import is_civfr_guild_or_mp

ANTIBOT_CHANNEL_ID = 1504089829770657873
ANTIBOT_REPORT_CHANNEL_ID = 830354347467735060
TROLL_MSG = [
    "On ne pourra pas tester son super jeu de vaisseau :'(",
    "Dommage pour tout l'argent du concours secret Mr. Beast ...",
    "Le prince nigériens va devoir chercher un nouveau héritier ...",
    "Pourtant il avait raison, j'avais de l'argent sur mon compte personnel de formation.",
    "J'espère qu'il ne vas pas signaler par erreur mon compte Steam.",
    "Visiblement, la haute-cour de CivFR ne veut pas vous faire profiter des super serveur discord top secret."
]

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

async def on_message_antibot(client : nextcord.Client, message : nextcord.Message):
    if message.channel == ANTIBOT_CHANNEL_ID:
        ban_report_channel = client.get_channel(ANTIBOT_REPORT_CHANNEL_ID)
        try:
            await message.author.ban(delete_message_days=1, reason="AntiBot channel - Autoban")
        except nextcord.HTTPException as e:
            await ban_report_channel.send(f"Erreur lors du bannisement automatique de <@{message.author.id}>: {e}")
        else:
            await ban_report_channel.send(f"[Anti-bot] <@{message.author.id}> a posté dans le channel interdit et a été banni: {random.choice(TROLL_MSG)}")