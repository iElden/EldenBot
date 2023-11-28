from __future__ import annotations
import logging
from trueskill import Rating, TrueSkill
from typing import Dict, List, Iterable

import Commands.CivFR.Database as DB
from Commands.CivFR.constant import MU, SIGMA, BETA, TAU, SKILL

logger = logging.getLogger("RankCalculator")

class RankPreviewer:
    env = TrueSkill(mu=MU, sigma=SIGMA, beta=BETA, tau=TAU, draw_probability=0.01)

    @classmethod
    def get_current_rank_for_players(cls, report) -> List[Rating]:
        return [DB.db.get_s1_player_stats(pl).get_rating() for pl in
                report.players]

    @classmethod
    def calc_new_ranks(cls, report : DB.RankedMatch, old_ranks : List[Rating]) -> List[Rating]:
        try:
            if report.scrapped:
                return [Rating(mu=i.mu-5, sigma=i.sigma) for i in old_ranks]
            new_ranks = cls.to_1d(
                cls.env.rate([(i,) for i in old_ranks], ranks=[pos for pos in report.players_pos.values()])
            )
            nb_player = len(report.players)
            for i, (player_id, old_r, new_r) in enumerate(zip(report.players, old_ranks, new_ranks)): # Top 3 can't lose point
                if nb_player > 6 and report.players_pos[player_id] <= 3 and new_r.mu < old_r.mu:
                    new_ranks[i] = Rating(mu=old_r.mu + 1, sigma=old_r.sigma)
                elif nb_player > 6 and report.players_pos[player_id] >= nb_player-3 and new_r.mu > old_r.mu:
                    new_ranks[i] = Rating(mu=old_r.mu - 1, sigma=old_r.sigma)
        except ValueError as e:
            logger.error(f"{type(e).__name__}: {e}")
            return old_ranks
        return new_ranks

    @classmethod
    def get_ranks_preview(cls, report) -> Dict[int, float]:
        old_ranks = cls.get_current_rank_for_players(report)
        new_ranks = cls.calc_new_ranks(report, old_ranks)
        return dict(zip(report.players, [SKILL(new) - SKILL(old) for new, old in zip(new_ranks, old_ranks)]))

    @staticmethod
    def to_1d(ls : List[Iterable]) -> List:
        return sum((list(i) for i in ls), [])