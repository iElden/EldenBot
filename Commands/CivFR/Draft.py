from typing import List
import random

from util.exception import InvalidArgs, NotFound
from .Leaders import leaders

PERSONA_BANS = ["franceeleonore", "teddyroughrider", "catherinemagnifique"]
RF_BANS = ["cris", "paysbas", "georgie", "chandragupta", "coree", "mapuches", "mongolie", "ecosse", "zoulous"]
GS_BANS = ["hongrie", "maoris", "canada", "incas", "mali", "suede", "ottomans", "phenicie", "angleterreeleonore", "franceeleonore"]
DLC_BANS = ["azteques", "pologne", "australie", "perse", "macedoine", "nubie", "khmer", "indonesie"]
NFP_BANS = ["mayas", "ethiopie", "catherinemagnifique", "teddyroughrider"]
SPECIAL_BANS = {
    "persona": PERSONA_BANS,
    "r&f": RF_BANS,
    "gs": GS_BANS,
    "dlc": DLC_BANS,
    "nfp": NFP_BANS,
    "vanillaonly": RF_BANS + GS_BANS + DLC_BANS + NFP_BANS
}

def get_draft(nb : int, *args, client) -> List[str]:
    pool = leaders.leaders[:]
    if len(args) >= 1:
        ban_query = args[0].split('.')
        for ban in ban_query:
            if not ban:
                continue
            sp = SPECIAL_BANS.get(ban.lower())
            if sp:
                for i in sp:
                    pool.remove(leaders.get_leader_named(i))
            else:
                lead = leaders.get_leader_named(ban)
                if not lead:
                    raise InvalidArgs(f"Leader \"{ban}\" non trouvé")
                pool.remove(lead)
    leader_per_player = len(pool) // nb
    if len(args) >= 2:
        if args[1] != 'max':
            if not args[1].isdigit():
                raise InvalidArgs(
                    "3rd Argument (max civ per draft) must be a integer or \"max\" (exemple: ``/draft 8 Maori.Colombie 4``)")
            leader_per_player = int(args[1])
    random.shuffle(pool)
    return [','.join(f"{client.get_emoji(j.emoji_id)} {j.civ}" for j in
               pool[i * leader_per_player:i * leader_per_player + leader_per_player]) for i in range(nb)]

async def get_member_in_channel(channel):
    if not channel:
        raise NotFound("Impossible de récupérer les joueurs : Vous n'êtes pas connecté à un channel vocal")
    return channel.members

class CmdCivDraft:
    async def cmd_draft(self, *args : str, channel, client, member, **_):
        if not args:
            raise InvalidArgs("Command should take at least one parameter")
        if args[0].lower() == 'ffa':
            members = await get_member_in_channel(member.voice.channel)
            nb = len(members)
            generator = (m.mention for m in members)
        else:
            if not args[0].isdigit():
                raise InvalidArgs("1st Argument must be a integer (exemple: ``/draft 2``) or 'FFA'")
            nb = int(args[0])
            generator = (f"n°{i+1}" for i in range(nb))
        drafts = get_draft(nb, *args[1:], client=client)

        result = []
        for i, g in enumerate(generator):
            result.append(f"{g} | {drafts[i]}")
        txt = ""
        for r in result:
            if len(txt) + len(r) >= 2000:
                await channel.send(txt)
                txt = r
            else:
                txt += '\n' + r
        await channel.send(txt)