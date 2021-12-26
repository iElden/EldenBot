import random
import nextcord
import re
from typing import List, Tuple
from util.exception import InvalidArgs


def roll_dice(nb, face):
    l = []
    for i in range(nb):
        l.append(random.randint(1,face))
    return l

class Dice:
    def __init__(self, nb, faces, negative):
        self.nb = nb # type: int
        self.faces = faces #type: int
        self.is_negative = negative #type: bool
    def __repr__(self):
        return f"Dice({self.nb}, {self.faces}, {self.is_negative})"
    def __str__(self):
        return f"{'-' if self.is_negative else ''}{self.nb}d{self.faces}"
    def roll(self):
        return [random.randint(-self.faces, -1) if self.is_negative else random.randint(1, self.faces) for _ in range(self.nb)]

class RollResult:
    def __init__(self, dices, results, bonus):
        self.dices = dices # type: List[Dice]
        self.results = results # type: List[List[int]]
        self.total = sum([sum(result) for result in results]) + bonus # type: int
        self.bonus = bonus
        self.is_bonus = bonus > 0 # type: bool
        self.bonus_value = abs(bonus)

    @property
    def format_results(self):
        return ' ; '.join([', '.join([f"**{i}**" for i in result]) for result in self.results])

    @property
    def intro_sentence(self):
        if not self.dices:
            dice_rolled = "Aucun dé"
        elif len(self.dices) == 1:
            dice_rolled = str(self.dices[0])
        else:
            dice_rolled = ', '.join(str(i) for i in self.dices[:-1]) + " et " + str(self.dices[-1])
        bonus = f" avec un {'bonus' if self.is_bonus else 'malus'} de {self.bonus_value}" if self.bonus else ""
        return f"a lancé {dice_rolled}{bonus} et a obtenu:"

def roll(expr : str) -> RollResult:
    dices, bonus = parse_expr(expr)
    return RollResult(dices, [i.roll() for i in dices], bonus)

def parse_expr(expr : str) -> Tuple[List[Dice], int]:
    dices = [] # type: List[Dice]
    bonus = 0  # type: int

    expr.replace(' ', '').lower()
    ex_list = re.split(r"([\+-])", expr)
    if ex_list[0] == '':
        del ex_list[0]
    else:
        ex_list.insert(0, '+')
    ex_list = [(ex_list[i * 2] + ex_list[i * 2 + 1]) for i in range(len(ex_list)//2)]
    for ex in ex_list:
        r = re.findall(r"^([\+-])?(\d+)d(\d+)$", ex)
        b = re.findall(r"^([\+-])?(\d+)$", ex)
        if r:
            r = r[0]
            if r[1] == '0':
                raise InvalidArgs("Le nombre de dé à lancer ne peut pas être égal à 0.")
            if r[2] == '0':
                raise InvalidArgs("Le dé ne peut pas avoir 0 face ... c'est physiquement impossible !")
            dices.append(Dice(int(r[1]), int(r[2]), r[0] == '-'))
        elif b:
            b = b[0]
            bonus += int(b[0] + b[1])
        else:
            raise InvalidArgs(f"L'expression \"{ex}\" ne correspond pas à une formule connu, consultez le ``/help Roll``")
    return dices, bonus


class CmdRoll:
    async def cmd_roll(self, *args, message, member, **_):
        if not args or not args[0]:
            args = "1d100"
        expr = "".join(args)
        r = roll(expr)
        await message.channel.send(embed=nextcord.Embed(
            title="Lancé de dés",
            description=f"{member.mention} {r.intro_sentence}\n\n{r.format_results}\n\nTotal : **{r.total}**",
            colour=member.colour
        ).set_footer(text=message.content).set_author(name=member.name, icon_url=member.avatar_url))
        try:
            await message.delete()
        except nextcord.HTTPException:
            pass

    async def cmd_bloodlustroll(self, *args, message, **_):
        arg = "".join(args).replace(" ","")
        if '+' in arg :
            r = int(arg.split('+')[1])
            d = int(arg.split('+')[0])
        else :
            d = int(arg)
            r = 0
        l = roll_dice(d ,6)
        await message.channel.send(embed=nextcord.Embed(title="Lancé de dés (Bloodlust)",description="{} a lancé {} dés avec {} risques, il a obtenu :\n\n**{}**\n\nTotal : **{}** (Qualités : **{}**)".format(message.author.name,str(d),str(r),", ".join([str(i) for i in l]),sum(l),str(len([i for i in l if i%2 == 0])+r)),colour=message.author.color).set_author(name=message.author.name,icon_url=message.author.avatar_url))
        try:
            await message.delete()
        except nextcord.HTTPException:
            pass

    async def cmd_r(self, *args, **kwargs): await self.cmd_roll(*args, **kwargs)
    async def cmd_br(self, *args, **kwargs): await self.cmd_bloodlustroll(*args, **kwargs)
    async def cmd_rb(self, *args, **kwargs): await self.cmd_bloodlustroll(*args, **kwargs)
