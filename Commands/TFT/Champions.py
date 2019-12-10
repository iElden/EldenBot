from abc import abstractmethod
from typing import Dict, Any
from constant.rgapi import CHAMP_NAME_TO_ID, CHAMP_ID_TO_EMOJI, CHAMP_NONE_EMOJI


class Champion:
    @classmethod
    def build_from_json(cls, dic):
        return cls(dic['name'], dic['level'])

    def __init__(self, champion_name, level):
        self.name = champion_name
        self.level = level
        self.current_mana = 0

    def __eq__(self, other):
        return self.name == other.name and self.level == other.level

    def to_json(self) -> Dict[str, Any]:
        return {'name': self.name, 'level': self.level}

    def to_emoji(self) -> str:
        return CHAMP_ID_TO_EMOJI.get(CHAMP_NAME_TO_ID.get(self.name, "0"), CHAMP_NONE_EMOJI)

    @abstractmethod
    def attack(self):
        ...

    @abstractmethod
    def spell(self):
        ...


class KhaZix(Champion):
    def __init__(self, level):
        super().__init__("Kha'Zix", level)