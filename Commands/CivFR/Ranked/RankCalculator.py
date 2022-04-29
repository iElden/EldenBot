from __future__ import annotations
import logging
from trueskill import Rating, TrueSkill
from typing import Dict, List, Iterable

import Commands.CivFR.Database as DB
from Commands.CivFR.constant import MU, SIGMA, BETA, TAU

logger = logging.getLogger("RankCalculator")

def SKILL(rating : Rating) -> float:
    return rating.mu - max(rating.sigma - 50, 0)

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
                return [Rating(mu=i.mu-20, sigma=i.sigma) for i in old_ranks]
            new_ranks = cls.to_1d(
                cls.env.rate([(i,) for i in old_ranks], ranks=[pos for pos in report.players_pos.values()])
            )
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