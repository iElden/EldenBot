from trueskill import Rating
import asyncio

from .RankCalculator import RankPreviewer
import Commands.CivFR.Database as DB
from Commands.CivFR.constant import SKILL

async def update_player_ranks(match : DB.RankedMatch):
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
        print("prout")
        # await asyncio.create_task(self.recalc_rank_role_by_id(player.id))