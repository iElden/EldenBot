import discord
import asyncio
from util.exception import NotFound

from typing import List

SERIOUS_VOTE_ID = 777985939020578886
CASUAL_VOTE_ID = 705685176176607282
BBGTEAM_ROLE_ID = 776858484108296192
SPECIALIST_ROLE_ID = 438521431698178058

class VoteDisplay:
    def __init__(self, message, reaction_users : List[List[discord.Member]]):
        self.message = message
        self.reactions = message.reactions
        self.reaction_users = reaction_users
        self.total_bbg_team = self.get_total_group(reaction_users, BBGTEAM_ROLE_ID)
        self.total_specialist = self.get_total_group(reaction_users, SPECIALIST_ROLE_ID)
        self.total_citizen = self.get_total_citizen(reaction_users)

    def get_total_group(self, reaction_users, role_id) -> set:
        r = set()
        for user in sum(reaction_users, []):
            if isinstance(user, discord.Member) and role_id in [role.id for role in user.roles]:
                r.add(user.id)
        return r

    def get_total_citizen(self, reaction_users) -> set:
        r = set()
        for user in sum(reaction_users, []):
            if isinstance(user, discord.User):
                r.add(user.id)
                continue
            roles = [role.id for role in user.roles]
            if SPECIALIST_ROLE_ID not in roles and BBGTEAM_ROLE_ID not in roles:
                r.add(user.id)
        return r

    def to_embed(self) -> discord.Embed:
        em = discord.Embed(title="Vote result", description=self.message.content)
        for name, ids in [("BBGTeam", self.total_bbg_team), ("Specialist", self.total_specialist), ("Citizen", self.total_citizen)]:
            ls = [f"{str(reaction)} : {self.get_count_str(members, ids)}"
                  for (reaction, members) in zip(self.reactions, self.reaction_users)]
            em.add_field(name=name, value='\n'.join(ls))
        return em

    def get_count_str(self, members, ids) -> str:
        members = [i.id for i in members if i.id in ids]
        if not members:
            return "0 (0%)"
        if len(members) > 2:
            return f"{len(members)} ({len(members)/len(ids):.1%})"
        members_mention = [f"<@{i}>" for i in members]
        return f"{len(members)} ({len(members)/len(ids):.1%};{''.join(members_mention)})"


class CmdBBGDisplayVote:

    async def diplay_vote(self, message, channel):
        vd = VoteDisplay(message, await asyncio.gather(*(reaction.users().flatten() for reaction in message.reactions)))
        await channel.send(embed=vd.to_embed())

    async def cmd_bbgdisplayvote(self, *args, client, channel, **_):
        target = int(args[0])
        for vote_channel_id in [SERIOUS_VOTE_ID, CASUAL_VOTE_ID]:
            vote_channel : discord.TextChannel = client.get_channel(vote_channel_id)
            message = await vote_channel.fetch_message(target)
            if message:
                break
        else:
            raise NotFound(f"Can't find message in channel <#{SERIOUS_VOTE_ID}> <#{CASUAL_VOTE_ID}>")
        await self.diplay_vote(message, channel)



    async def cmd_bbgdisplayvotefrom(self,  *args, client, channel, **_):
        target = int(args[0])
        for vote_channel_id in [SERIOUS_VOTE_ID, CASUAL_VOTE_ID]:
            vote_channel : discord.TextChannel = client.get_channel(vote_channel_id)
            try:
                message = await vote_channel.fetch_message(target)
            except discord.HTTPException:
                message = None
            if message:
                break
        else:
            raise NotFound(f"Can't find message in channel <#{SERIOUS_VOTE_ID}> <#{CASUAL_VOTE_ID}>")
        history = await message.channel.history(after=message).flatten()
        for msg in history:
            await self.diplay_vote(msg, channel)
