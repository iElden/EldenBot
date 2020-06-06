import random

from util.exception import InvalidArgs
from .Leaders import leaders


class CmdCivFR:
    async def cmd_draft(self, *args : str, channel, client, **_):
        if not args:
            raise InvalidArgs("Command should take at least one parameter")
        if not args[0].isdigit():
            raise InvalidArgs("1st Argument must be a integer (exemple: ``/draft 2``)")
        pool = leaders.leaders[:]
        if len(args) >= 2:
            ban_query = args[1].split('.')
            for ban in ban_query:
                lead = leaders.get_leader_named(ban)
                if not lead:
                    raise InvalidArgs(f"Leader \"{ban}\" non trouvé")
                pool.remove(lead)
        nb = int(args[0])
        random.shuffle(pool)
        leader_per_player = len(pool) // nb
        result = []
        for i in range(nb):
            g = (f"{client.get_emoji(j.emoji_id)} {j.uuname.title()}" for j in pool[i*leader_per_player:i*leader_per_player+leader_per_player])
            result.append(f"n°{i+1} | {', '.join(g)}")
        txt = ""
        for r in result:
            if len(txt) + len(r) >= 2000:
                await channel.send(txt)
                txt = r
            else:
                txt += '\n' + r
        await channel.send(txt)