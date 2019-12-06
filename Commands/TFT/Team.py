from .Champions import Champion

from typing import List, Optional
from util.exception import ALEDException

class Team:
    def __init__(self, champions : List[Champion]):
        self.champions = champions

    def to_json(self):
        return [i.to_json() for i in self.champions]

    def mix_3_champs(self, champion) -> Optional[Champion]:
        nb = self.champions.count(champion)
        if nb > 3:
            raise ALEDException("A player has more than 3 champions, this situation should never occurs ! DATABASE CORRUPTED !")
        elif nb == 3:
            while champion in self.champions: self.champions.remove(champion)
            new_champ = Champion(champion.name, champion.level + 1)
            self.champions.append(new_champ)
            return new_champ
        return None