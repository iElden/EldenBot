import discord
import asyncio
from typing import List, Iterable, Dict, Optional
import random

from util.exception import InvalidArgs
from util.function import get_member_in_channel
from .Leaders import leaders, Leader

PERSONA_BANS = ["franceeleonore", "teddyroughrider", "catherinemagnifique"]
RF_BANS = ["cris", "paysbas", "georgie", "chandragupta", "coree", "mapuches", "mongolie", "ecosse", "zoulous"]
GS_BANS = ["hongrie", "maoris", "canada", "incas", "mali", "suede", "ottomans", "phenicie", "angleterreeleonore", "franceeleonore"]
DLC_BANS = ["azteques", "pologne", "australie", "perse", "macedoine", "nubie", "khmer", "indonesie"]
NFP_BANS = ["mayas", "ethiopie", "catherinemagnifique", "teddyroughrider"]
SPECIAL_BANS = {
    "persona": PERSONA_BANS,
    "r&f": RF_BANS,
    "gs": GS_BANS,
    "dlc": DLC_BANS,
    "nfp": NFP_BANS,
    "vanillaonly": RF_BANS + GS_BANS + DLC_BANS + NFP_BANS
}

def get_raw_draft(nb : int, *args) -> Iterable[List[Leader]]:
    pool = leaders.leaders[:]
    if len(args) >= 1:
        ban_query = args[0].split('.')
        for ban in ban_query:
            if not ban:
                continue
            sp = SPECIAL_BANS.get(ban.lower())
            if sp:
                for i in sp:
                    pool.remove(leaders.get_leader_named(i))
            else:
                lead = leaders.get_leader_named(ban)
                if not lead:
                    raise InvalidArgs(f"Leader \"{ban}\" non trouvé")
                pool.remove(lead)
    leader_per_player = len(pool) // nb
    if len(args) >= 2:
        if args[1] != 'max':
            if not args[1].isdigit():
                raise InvalidArgs(
                    "3rd Argument (max civ per draft) must be a integer or \"max\" (exemple: ``/draft 8 Maori.Colombie 4``)")
            leader_per_player = int(args[1])
    random.shuffle(pool)
    return (pool[i * leader_per_player:i * leader_per_player + leader_per_player] for i in range(nb))

def get_draft(nb : int, *args, client) -> List[str]:
    pools = get_raw_draft(nb, *args)
    return [','.join(f"{client.get_emoji(j.emoji_id)} {j.civ}" for j in pool) for pool in pools]

class BlindDraft:
    def __init__(self, members, *args):
        self.members = members
        self.pools = [i[:20] for i in get_raw_draft(len(members), *args)]
        self.pool_per_member = {k.id: v for k, v in zip(self.members, self.pools)}  # type: Dict[int, List[Leader]]
        self.picks = {k.id: None for k in self.members}  # type: Dict[int, Optional[Leader]]

    async def run(self, channel : discord.TextChannel, client):
        msg = await channel.send(embed=discord.Embed(title="Blind draft", description="Envoie des drafts en cours !"))
        tasks = (self.send_bdrafts(member, pool, client=client) for member, pool in zip(self.members, self.pools))
        mps = await asyncio.gather(*tasks)
        mp_per_member = {k.id: v for k, v in zip(self.members, mps)}

        def check(reac_ : discord.Reaction, user_ : discord.User):
            return (user_.id in mp_per_member.keys() and
                    reac_.message.id in (i.id for i in mp_per_member.values()))

        await msg.edit(embed=self.get_embed(client=client))
        while True:
            reaction, user = await client.wait_for('reaction_add', check=check)
            leader = leaders.get_leader_by_emoji_id(reaction.emoji.id)
            if leaders.get_leader_by_emoji_id(reaction.emoji.id) not in self.pool_per_member[user.id]:
                continue
            self.picks[user.id] = leader
            await msg.edit(embed=self.get_embed(client=client))
            if self.is_finished:
                return

    @staticmethod
    async def send_bdrafts(member, pool, *, client):
        em = discord.Embed(title="Blind Draft",
                           description='\n'.join(f"{client.get_emoji(i.emoji_id)} {i.civ}" for i in pool))
        em.add_field(name="Status", value="Cliquez sur une réaction pour choisir votre leader")
        msg = await member.send(embed=em)
        tasks = (msg.add_reaction(client.get_emoji(i.emoji_id)) for i in pool)
        await asyncio.gather(*tasks)
        return msg

    @staticmethod
    async def edit_bdrafts(message, pool, *, client):
        em = discord.Embed(title="Blind Draft",
                           description='\n'.join(f"{client.get_emoji(i.emoji_id)} {i.civ}" for i in pool))
        em.add_field(name="Status", value="Vous avez choisis votre Leader !")
        await message.edit(embed=em)

    def get_embed(self, *, client):
        em = discord.Embed(title="Blind Draft")
        em.add_field(name="Joueurs", value='\n'.join(f"<@{i}>" for i in self.picks.keys()))
        if self.is_finished:
            em.add_field(name="Picks",
                         value='\n'.join(f"{client.get_emoji(i.emoji_id)} {i.civ}" for i in self.picks.values()))
        else:
            em.add_field(name="Picks",
                         value='\n'.join(("En attente ..." if i is None else "Sélectionné") for i in self.picks.values()))
        return em

    @property
    def is_finished(self):
        return None not in self.picks.values()


async def draw_draft(drafts, generator, channel):
    result = []
    for i, g in enumerate(generator):
        result.append(f"{g} | {drafts[i]}")
    txt = ""
    for r in result:
        if len(txt) + len(r) >= 2000:
            await channel.send(txt)
            txt = r
        else:
            txt += '\n' + r
    await channel.send(txt)

# COMMAND
class CmdCivDraft:
    async def cmd_draft(self, *args : str, channel, client, member, **_):
        if not args:
            raise InvalidArgs("Command should take at least one parameter")
        if args[0].lower() == 'ffa':
            members = get_member_in_channel(member.voice)
            nb = len(members)
            generator = (m.mention for m in members)
        else:
            if not args[0].isdigit():
                raise InvalidArgs("1st Argument must be a integer (exemple: ``/draft 2``) or 'FFA'")
            nb = int(args[0])
            generator = (f"n°{i+1}" for i in range(nb))
        drafts = get_draft(nb, *args[1:], client=client)
        await draw_draft(drafts, generator, channel)


    async def cmd_blinddraft(self, *args : str, channel, client, member, **_):
        bd = BlindDraft(get_member_in_channel(member.voice), *args)
        await bd.run(channel, client=client)

    async def cmd_dbgblinddraft(self, *args : str, channel, client, member, **_):
        bd = BlindDraft([member, client.get_user(267018917589942273)], *args)
        await bd.run(channel, client=client)

