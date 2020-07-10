import random
import discord

from util.exception import InvalidArgs
from .Leaders import leaders

def get_draft(nb : int, *args, client):
    pool = leaders.leaders[:]
    if len(args) >= 1:
        ban_query = args[0].split('.')
        for ban in ban_query:
            if not ban:
                continue
            lead = leaders.get_leader_named(ban)
            if not lead:
                raise InvalidArgs(f"Leader \"{ban}\" non trouvé")
            pool.remove(lead)
    if len(args) >= 2:
        if not args[1].isdigit():
            raise InvalidArgs(
                "3rd Argument (max civ per draft) must be a integer (exemple: ``/draft 8 Maori.Colombie 4``)")
        leader_per_player = int(args[1])
    else:
        leader_per_player = len(pool) // nb
    random.shuffle(pool)
    return [(f"{client.get_emoji(j.emoji_id)} {j.uuname.title()}" for j in
               pool[i * leader_per_player:i * leader_per_player + leader_per_player]) for i in range(nb)]


class CmdCivFRDraft:

    async def cmd_chuckdraft(self, *args : str, channel, client, **_):
        """/chuckdraft {nb} {bans} {leader_per_draft} {ban_per_team} {pick_per_team}"""
        if not args:
            raise InvalidArgs("Command should take at least one parameter")
        if not args[0].isdigit():
            raise InvalidArgs("1st Argument must be a integer (exemple: ``/chuckdraft 8``)")
        nb = int(args[0])
        drafts = get_draft(nb, *args[1:3], client=client)

        ban_per_team = 1
        if len(args) >= 4:
            if not args[3].isdigit():
                raise InvalidArgs(f"Number of ban per team must be a int, not \"{args[3]}\"")
            ban_per_team = int(args[3])
        pick_per_team = (len(drafts) - ban_per_team * 2) // 2
        if len(args) >= 5:
            if not args[4].isdigit():
                raise InvalidArgs(f"Number of pick per team must be a int, not \"{args[4]}\"")
            pick_per_team = int(args[4])
            if pick_per_team > (len(drafts) - ban_per_team * 2) // 2:
                raise InvalidArgs(f"There is not enough draft for this number of ban/pick per team")

        em = discord.Embed(title="blabla")