import nextcord
from trueskill import Rating
from typing import List
import asyncio

from .RankCalculator import RankPreviewer
import Commands.CivFR.Database as DB
from Commands.CivFR.constant import SKILL, RANKED_LOG_CHANNEL

async def update_player_ranks(match : DB.RankedMatch, client : nextcord.Client=None):
    print("===================================")
    old_ranks = RankPreviewer.get_current_rank_for_players(match)
    new_ranks = RankPreviewer.calc_new_ranks(match, old_ranks)
    print(old_ranks, new_ranks)
    for (player_id, pos), old_rank, rank in zip(match.players_pos.items(), old_ranks, new_ranks):
        print(player_id, pos, old_rank, rank)
        stat : DB.RankedStats2 = DB.db.get_s1_player_stats(player_id)
        # Update player stats
        stat.mu = rank.mu
        stat.sigma = rank.sigma
        stat.games += 1
        stat.wins += SKILL(rank) >= SKILL(old_rank)
        stat.first += pos == 1
        DB.db.update_s1_player_stats(stat)
        # await asyncio.create_task(self.recalc_rank_role_by_id(player.id))
    if client:
        await send_debug_points_report(match, old_ranks, new_ranks, client)

async def send_debug_points_report(match : DB.RankedMatch, old_ranks : List[Rating], new_ranks : List[Rating], client : nextcord.Client):
    txt = "__**POINT UPDATE**__"
    channel = client.get_channel(RANKED_LOG_CHANNEL)
    for (player_id, pos), old_rank, rank in zip(match.players_pos.items(), old_ranks, new_ranks):
        txt += f"\n\n<@{player_id}> :\nMu   : {old_rank.mu:.2f} => {rank.mu:.2f}\nSigma: {old_rank.sigma:.2f} => {rank.sigma:.2f}\nSkill: {SKILL(old_rank)} => {SKILL(rank)}"
    await channel.send(txt)