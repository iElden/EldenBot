import logging
from trueskill import Rating
from typing import Dict

logger = logging.getLogger("RankCalculator")

class RankPreviewer:
    from typing import List, Iterable
    from Commands.CivFR.Database import RankedMatch, db

    @classmethod
    def get_current_rank_for_players(cls, report : RankedMatch) -> List[Rating]:
        return [cls.db.get_s1_player_stats(pl).get_rating() for pl in
                report.players]

    @classmethod
    def calc_new_ranks(cls, report : RankedMatch, old_ranks : List[Rating]) -> List[Rating]:
        try:
            new_ranks = cls.to_1d(
                cls.ranked_module.env.rate([(i,) for i in old_ranks], ranks=[pos for pos in report.players_pos.values()])
            )
        except ValueError as e:
            logger.error(f"{type(e).__name__}: {e}")
            return old_ranks
        return new_ranks

    @classmethod
    def get_ranks_preview(cls, report : RankedMatch) -> Dict[int, float]:
        old_ranks = cls.get_current_rank_for_players(report)
        new_ranks = cls.calc_new_ranks(report, old_ranks)
        return dict(zip(report.players, [SKILL(new) - SKILL(old) for new, old in zip(new_ranks, old_ranks)]))

    @staticmethod
    def to_1d(ls : List[Iterable]) -> List:
        return sum((list(i) for i in ls), [])