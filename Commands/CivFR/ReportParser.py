from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import discord
import re

from util.exception import NotFound, InvalidArgs
from .Leaders import Leader, leaders

class GameType(Enum):
    BEGIN_FFA = "FFA Débutant"
    BEGIN_TEAMER = "Teamer Débutant"
    FFA = "FFA Confirmé"
    TEAMER = "Teamer Confirmé"

MENTION = re.compile("<@!?(\d+)>\s*([^<]+)")

@dataclass
class GPlayer:
    id : int
    leader : Leader
    position : int

    def __repr__(self):
        return f"<GPlayer id: {self.id}, position: {self.position}, leader: {self.leader}>"

    def is_valid(self) -> bool:
        return bool(self.id and self.leader)

    def to_json(self):
        return {"id": self.id, "leader": self.leader and self.leader.uuname, "position": self.position}

    @classmethod
    def from_json(cls, js):
        return cls(js['id'], js['leader'], js['position'])

class Report:
    def __init__(self, gametype, players):
        self.gametype : Optional[GameType] = gametype
        self.players : List[GPlayer] = players

    def players_to_strings(self) -> str:
        return '\n'.join(f"{i.position}: <@{i.id}> {i.leader and i.leader.civ}" for i in self.players)

    def to_json(self) -> Dict[str, Any]:
        return {
            "gametype": self.gametype.value,
            "players": [i.to_json() for i in self.players]
        }

    @classmethod
    def from_json(cls, js):
        return cls(GameType(js['gametype']) if js['gametype'] else None,
                   [GPlayer(i['id'], leaders.get_leader_named(i['leader']), i['position']) for i in js['players']])

    @staticmethod
    def parse_ffa(txt) -> List[GPlayer]:
        result = []
        pos = 0
        for line in txt.split('\n'):
            ls = MENTION.findall(line)
            pos += len(ls)
            result.extend(GPlayer(int(discord_id), leaders.get_leader_named(value), pos) for discord_id, value in ls)
        return result

    @staticmethod
    def parse_teamer(txt) -> List[GPlayer]:
        result = []
        ls = [MENTION.findall(i) for i in txt.split('\n\n')]
        ls = [i for i in ls if i]
        pos = 1
        for i in ls:
            result.extend(GPlayer(int(d_id), leaders.get_leader_named(lead), pos) for d_id, lead in i)
            pos += 1
        return result

    @classmethod
    def from_str(cls, txt):
        gametype_query, corps = txt.split('\n', 1)
        gametype_query.lower()
        gametype = None
        for i in GameType:
            if i.value.lower() in gametype_query:
                gametype = i
        if gametype in [GameType.BEGIN_FFA, GameType.FFA]:
            players = cls.parse_ffa(corps)
        elif gametype in [GameType.BEGIN_TEAMER, GameType.TEAMER]:
            players = cls.parse_teamer(corps)
        else:
            players = []
            # raise NotFound(f"GameType don't match, please use one of the Following : {', '.join(i.value for i in GameType)}")
        # if not players:
        #     raise InvalidArgs("No player was mentionned in report")
        return cls(gametype, players)