import csv
from typing import List

class Leaders:
    def __init__(self, leaders_):
        self.leaders = leaders_

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

    def get_leader_by_emoji_id(self, emoji_id):
        for leader in self:
            if leader.emoji_id == emoji_id:
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
        if other is None:
            return False
        if isinstance(other, str):
            return other.lower() in self.all_name
        return self.uuname == other.uuname

def load_leaders():
    with open("data/leaders.csv", "r") as fd:
        leaders_array = csv.reader(fd, delimiter=',')
        leaders = Leaders([Leader(*leader_array) for leader_array in leaders_array])
        return leaders

leaders = load_leaders()
