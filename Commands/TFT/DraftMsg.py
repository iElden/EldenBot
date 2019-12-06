from typing import Dict, List
from constant.rgapi import CHAMP_ID_TO_EMOJI, CHAMP_NAME_TO_ID, TFT_PRICES, INVISIBLE_EMOJI
from .const import CHAMPIONS_PRICES
from .Champions import Champion
from util.exception import Forbidden
import discord

class DraftMsg:

    _all_messages = {}  # type: Dict[int, DraftMsg]

    @classmethod
    def get_msg(cls, message_id):
        return cls._all_messages.get(message_id, None)

    def __init__(self, champions_list):
        self.champions_list = champions_list
        self.picked = set()
        self.player_picked = set()
        self.logs = [f"Les champions sont apparus"]
        self.msg = None

    @classmethod
    async def create(cls, channel, champions_list):
        self = cls(champions_list)
        self.msg = await channel.send(embed=discord.Embed(title="Chargement"))
        await self.update()
        for i in range(len(champions_list)):
            await self.msg.add_reaction(str(i) + chr(0xFE0F) + chr(0x20E3))
        cls._all_messages[self.msg.id] = self


    async def update(self):
        price_emoji = [TFT_PRICES[CHAMPIONS_PRICES[champ]] for champ in self.champions_list]
        champ_emoji = [CHAMP_ID_TO_EMOJI[CHAMP_NAME_TO_ID[champ]] for champ in self.champions_list]
        number_list = [((str(i) + chr(0xFE0F) + chr(0x20E3)) if i not in self.picked else INVISIBLE_EMOJI)
                       for i in range(len(self.champions_list))]
        em = discord.Embed(title="Shared Draft", description="Cliquez sur les réactions pour prendre votre champion")
        em.add_field(name="Logs",
                     value='\n'.join(self.logs),
                     inline=False)
        await self.msg.edit(content=f"{' '.join(price_emoji)}\n{' '.join(champ_emoji)}\n{' '.join(number_list)}", embed=em)

    async def pick_champions(self, member, nb) -> Champion:
        if nb in self.picked or member.id in self.player_picked:
            raise Forbidden("vous ne pouvez choisir qu'une fois un champion")
        self.picked.add(nb)
        self.player_picked.add(member.id)
        self.logs.append(f"{member.display_name} a sélectionné {self.champions_list[nb]}")
        await self.update()
        return Champion(self.champions_list[nb], 1)