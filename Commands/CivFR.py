import csv
from typing import List
import random

from util.exception import InvalidArgs

class Leaders:
    def __init__(self, leaders):
        self.leaders = leaders

    def __getitem__(self, item):
        return self.leaders[item]

    def __iter__(self):
        for i in self.leaders:
            yield i

    def get_leader_named(self, name):
        for leader in self:
            if leader == name:
                return leader
        return None

class Leader:
    def __init__(self, emoji_id, uuname, name, civ, *alias):
        self.emoji_id = int(emoji_id)
        self.uuname = uuname
        self.name = name
        self.civ = civ
        self.alias = alias
        self.all_name = [i.lower() for i in [uuname, name, civ, *alias]]

    def __repr__(self):
        return f"<Leader: {self.uuname}>"

    def __eq__(self, other):
        if isinstance(other, str):
            return other.lower() in self.all_name
        return self.uuname == other.uuname

def load_leaders():
    with open("data/leaders.csv", "r") as fd:
        leaders_array = csv.reader(fd, delimiter=',')
        leaders = Leaders([Leader(*leader_array) for leader_array in leaders_array])
        return leaders

leaders = load_leaders()

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