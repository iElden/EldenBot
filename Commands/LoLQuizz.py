import requests
import nextcord
import random
import logging
import asyncio
from typing import Dict, Any, Tuple
from util.exception import InvalidArgs

logger = logging.getLogger("LoLQuizz")

def get_champion_full():
    logger.info("Initialising LoLQuizz Data")
    response = requests.get("http://ddragon.canisback.com/latest/data/en_US/championFull.json")
    logger.info("Done")
    return response.json()['data']  # type: Dict[str, Dict[str, Any]]

champion_full = get_champion_full()
BASE_URL_SPELL = "http://ddragon.canisback.com/latest/img/spell/"
BASE_URL_PASSIVE = "http://ddragon.canisback.com/latest/img/passive/"
EMBED_TITLE = "Find the spell"
LETTER_TO_N = {'q': 0, 'a': 0, 'w': 1, 'z': 1, 'e': 2, 'r': 3, 'p': 4}

class RandomSpell:
    def __init__(self, old=None):
        """

        Args:
            old (List[Tuple[str, int]]):
        """
        while True:
            champion = random.choice(list(champion_full.keys()))
            n = random.randint(0, 4)
            self.answer = (champion, n)
            if self.answer in old: continue
            if n == 4:
                self.name = champion_full[champion]['passive']['name']
                self.image_endurl = champion_full[champion]['passive']['image']['full']
            else:
                self.name = champion_full[champion]['spells'][n]['name']
                self.image_endurl = champion_full[champion]['spells'][n]['image']['full']
            self.champion = champion.lower().replace("'", "")
            self.simplified_name = self.name.lower().replace("'", '')
            if not self.simplified_name: continue
            break

    def __eq__(self, other):
        """
        Args:
            other (RandomSpell): other randomSpell

        Returns:
        """
        return self.answer == other.answer

    @property
    def image_url(self):
        if self.answer[1] == 4:
            return BASE_URL_PASSIVE + self.image_endurl
        return BASE_URL_SPELL + self.image_endurl

    def to_embed(self, *, with_image=False, footer_text=None):
        em = nextcord.Embed(title=EMBED_TITLE, description=self.name)
        if with_image:
            em.set_thumbnail(url=self.image_url)
        if footer_text:
            em.set_footer(text=footer_text)
        return em

    def check_if_correct(self, s) -> bool:
        s = s.lower().replace("'", '')
        str_list = s.split(' ')
        if len(str_list) < 2:
            return False
        champion = ''.join(str_list[:-1])
        if champion == "wukong":
            champion = "monkeyking"
        try:
            n = LETTER_TO_N[str_list[-1]]
        except:
            return False
        return self.champion == champion and self.answer[1] == n


class CmdLoLQuizz:
    async def cmd_lolquizz(self, *args, channel, client, **_):
        """
        Args:
            *args:
            channel (nextcord.TextChannel):
            **_:

        Returns:

        """
        if not args:
            max_question = 10
        else:
            try:
                max_question = int(''.join(args))
            except:
                raise InvalidArgs("Le nombre max de question doit être un nombre")
            if max_question > 500:
                raise InvalidArgs("Déso pas déso, le max c'est 500")

        points = {}
        old = []

        for current_question in range(max_question):
            second_time = False
            spell = RandomSpell(old=old)
            old.append(spell.answer)
            check = lambda m: m.channel == channel and spell.check_if_correct(m.content)

            while True:
                if not second_time:
                    msg = await channel.send(embed=spell.to_embed(
                        footer_text=f"question {current_question + 1}/{max_question}",
                        with_image=False
                    ))
                else:
                    await msg.edit(embed=spell.to_embed(
                        footer_text=f"question {current_question + 1}/{max_question}",
                        with_image=True
                    ))
                try:
                    answer = await client.wait_for('message', check=check, timeout=15)  # type: nextcord.Message
                except asyncio.TimeoutError:
                    second_time = True
                    continue
                points[answer.author.name] = points.get(answer.author.name, 0) + 1
                await channel.send(f"{answer.author.mention} a gagné un point" +
                                   "```{}```".format('\n'.join([f'{k} : {v}' for k, v in points.items()]))
                )
                break