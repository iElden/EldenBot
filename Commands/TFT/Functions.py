from .const import CHAMPIONS_PRICES, CHANNEL_ID
from .Database import Database
from .Champions import Champion
from .Team import Team
from .DraftMsg import DraftMsg

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
        if random.randint(1, 100) <= 5:
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
            team = Team(champ_list)
            await Functions.mix_if_3_champ(team, champion, channel=channel, member=member)
            db.update_champions(member.id, team.to_json())

    @staticmethod
    async def mix_if_3_champ(team, champion, *, channel, member):
        new_champ = team.mix_3_champs(champion)
        if new_champ:
            await channel.send(f"{member.mention} a obtenu {new_champ.name} au niveau {new_champ.level} !")
            await Functions.mix_if_3_champ(team, new_champ, channel=channel, member=member)
