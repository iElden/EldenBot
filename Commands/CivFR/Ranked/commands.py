import nextcord
from typing import List, Tuple, Dict
import asyncio

from .views import ReportView as views

from Commands.CivFR.Voting import Voting, RANKED_SETTINGS
from Commands.CivFR.constant import CIVFR_GUILD_ID, RANKED_CHANNEL
from Commands.CivFR.utils import is_arbitre
from Commands.CivFR.Database import db, RankedMatch
from constant import emoji
from util.exception import ALEDException, BotError, NotFound
from util.function import get_member_in_channel, get_member

async def on_reaction(payload : nextcord.RawReactionActionEvent, *, client : nextcord.Client):
    if payload.channel_id != RANKED_CHANNEL:
        return
    civfr: nextcord.Guild = client.get_guild(CIVFR_GUILD_ID)
    member : nextcord.Member = civfr.get_member(payload.user_id)
    if not member:
        raise ALEDException("Member not found on CivFR")
    ranked_match: RankedMatch = db.get_s1_match(payload.message_id)
    if str(payload.emoji) == emoji.TURKEY:
        if not views.member_is_authorised(member):
            return
        channel = client.get_channel(payload.channel_id)
        msg = channel.get_partial_message(payload.message_id)
        await msg.edit(view=views.RankedView(db.get_s1_match(msg.id), parent=msg, client=client))
    if str(payload.emoji) in emoji.NB:
        if payload.user_id not in ranked_match.players:
            return
        index = emoji.NB.index(str(payload.emoji))
        ranked_match.set_player_position(payload.user_id, index)
        await ranked_match.update_embed(client)
        db.update_s1_match(ranked_match)


class RankedGame:
    def __init__(self, players):
        self.players = players
        self.vote = None
        self.ranked_match : RankedMatch = None

    async def post_report(self, client : nextcord.Client):
        channel = client.get_channel(RANKED_CHANNEL)
        msg = await channel.send(content=self.ranked_match.get_players_mention_string(),
                                 embed=self.ranked_match.get_embed())
        self.ranked_match.id = msg.id
        for i in range(1, len(self.ranked_match.players)+1):
            await msg.add_reaction(emoji.NB[i])
        await msg.add_reaction(emoji.TURKEY)
        db.add_s1_match(self.ranked_match)

    async def run(self, channel, member, client):
        self.ranked_match = RankedMatch.new_game([i.id for i in self.players])
        asyncio.create_task(self.post_report(client))
        vote = Voting(self.players, RANKED_SETTINGS)
        await vote.run(channel, client)


class CmdCivFRRanked:
    async def cmd_rankedstats(self, *args, channel, member, guild, **_):
        if not args:
            target = member
        else:
            raise NotImplemented(emoji.OK + " Boire un café ")
        st = db.get_s1_player_stats(target.id)
        await channel.send(embed=st.to_embed())


    async def cmd_startranked(self, *args, channel, client, member, message, **_):
        players = await self.parse_vote_args(args, channel, member, message)
        rg = RankedGame(players)
        await rg.run(channel, member, client)

    @staticmethod
    async def parse_vote_args(args, channel, member, message):
        if not args:
            members = get_member_in_channel(member.voice)
        else:
            try:
                members = get_member_in_channel(member.voice)
            except:
                members = [member]
            diff_members = message.mentions
            added = []
            removed = []
            for member in diff_members:
                if member in members:
                    removed.append(member)
                    members.remove(member)
                else:
                    added.append(member)
                    members.append(member)
            if removed:
                await channel.send("The following player has been removed from the vote: " + ', '.join(i.mention for i in removed))
            if added:
                await channel.send("The following player has been added to the vote: " + ', '.join(i.mention for i in added))
        if not members:
            raise BotError("Trying to run a vote without members")
        return members
