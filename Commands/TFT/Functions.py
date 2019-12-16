from .const import CHAMPIONS_PRICES, CHANNEL_ID
from .Database import Database
from .Champions import Champion
from .Team import Team
from .DraftMsg import DraftMsg
from util.exception import InvalidArgs, NotFound

import random
import discord
from typing import List
import logging

logger = logging.getLogger("TFT")


class Functions:

    @staticmethod
    def random_champions(nb=10):
        champ_list = sum([[k] * (6 - v) for k, v in CHAMPIONS_PRICES.items()], [])
        return random.choices(champ_list, k=nb)

    @staticmethod
    async def on_champion_pick(payload : discord.RawReactionActionEvent, *, client):
        draft_msg = DraftMsg.get_msg(payload.message_id)
        if not draft_msg:
            return None
        guild = client.get_guild(payload.guild_id)  # type: discord.Guild
        member = guild.get_member(payload.user_id)  # type: discord.Member
        channel = client.get_channel(payload.channel_id)  # type: discord.TextChannel
        champion = await draft_msg.pick_champions(member, int(str(payload.emoji)[0]))
        await Functions.add_champion(member, champion.name, channel=channel)

    @staticmethod
    async def routine(*, client):
        logger.debug("Entering TFT.routine")
        if random.randint(1, 100) <= 10:
            logger.info("Spawning TFT draft")
            await Functions.spawn_draft(client.get_channel(CHANNEL_ID))

    @staticmethod
    async def spawn_draft(channel):
        champion_list = Functions.random_champions(10)
        await DraftMsg.create(channel, champion_list)


    @staticmethod
    async def add_champion(member, champion_name, *, channel):
        champion = Champion(champion_name, 1)
        with Database() as db:  # type: Database
            champ_json = db.get_champions(member.id)
            champ_list = [Champion.build_from_json(i) for i in champ_json]  #type: List[Champion]

            champ_list.append(champion)
            team = Team(champ_list, member)
            await Functions.mix_if_3_champ(team, champion, channel=channel, member=member)
            db.update_champions(member.id, team.to_json())

    @staticmethod
    async def mix_if_3_champ(team, champion, *, channel, member):
        new_champ = team.mix_3_champs(champion)
        if new_champ:
            await channel.send(f"{member.mention} a obtenu {new_champ.name} au niveau {new_champ.level} !")
            await Functions.mix_if_3_champ(team, new_champ, channel=channel, member=member)

    @staticmethod
    async def sell_champ(*args, channel, member):
        if len(args) < 2:
            raise InvalidArgs("/tftsell {nom du champion} {niveau}")
        if not args[-1].isdigit():
            raise InvalidArgs(f"Le niveau doit être un nombre et non \"{args[-1]}\"")
        champion = ' '.join(args[:-1])
        level = int(args[-1])
        d = {"name": champion, "level": level}
        if champion not in CHAMPIONS_PRICES.keys():
            raise NotFound(f"Le champion nommé \"{champion}\" n'est pas disponible dans ce set")
        with Database() as db:  # type: Database
            champ_json = db.get_champions(member.id)
            if not champ_json:
                raise NotFound(f"No champion found for {member}")
            if d not in champ_json:
                raise NotFound(f"Champion {champion} lvl: {level} non trouvé dans l'équipe")
            champ_json.remove(d)
            gold = db.get_gold(member.id)
            gain = CHAMPIONS_PRICES[champion] * 3 ** (level - 1)
            db.update_gold(member.id, gold + gain)
            db.update_champions(member.id, champ_json)
        await channel.send(f"{member.mention} a vendu {champion} lvl {level} pour {gain} gold ({gold + gain})")
