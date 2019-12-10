from .Champions import Champion

import discord
from typing import List, Optional
from util.exception import ALEDException

class Team:
    def __init__(self, champions : List[Champion], owner : Optional[discord.Member]):
        self.champions = champions
        self.owner = owner

    @classmethod
    def from_json(cls, champion_list, member=None):
        champions = [Champion.build_from_json(i) for i in champion_list]
        return cls(champions, member)

    def to_json(self):
        return [i.to_json() for i in self.champions]

    def to_embed(self) -> discord.Embed:
        if not self.champions:
            return discord.Embed(title="Champions", description="Vous n'avez aucun champion")
        em = discord.Embed(title="Champions", colour=self.owner.colour)
        for level in range(self.champions[0].level, 0, -1):
            em.add_field(name=f"Niveau {level}",
                         value=''.join([i.to_emoji() for i in self.champions if i.level == level])[:1000],
                         inline=False)
        em.set_author(name=self.owner.name, icon_url=self.owner.avatar_url)
        return em



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