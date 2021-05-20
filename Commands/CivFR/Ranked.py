from trueskill import TrueSkill, Rating
from typing import List, Tuple, Dict

from .Database import db
from .ReportParser import GameType


MU = 1400
SIGMA = MU / 3
BETA = SIGMA / 2
TAU = SIGMA / 100

class PlayerStat:
    def __init__(self, discord_id : int, rating : Rating, win, lose):
        self.discord_id : int = discord_id
        self.rating : Rating = rating
        self.win = win
        self.lose = lose

    @property
    def elden(self):
        return self.rating.mu - max(self.rating.sigma - 150, 0)

class RankedModule:
    def __init__(self):
        self.env = TrueSkill(mu=MU, sigma=SIGMA, beta=BETA, tau=TAU, draw_probability=0.01)
        self.player_cache : Dict[int, PlayerStat]= {}

    def get_player(self, discord_id):
        return self.player_cache.get(discord_id, PlayerStat(discord_id, self.env.Rating(mu=MU), 0, 0))

    def rate_teamer(self, win_team : List[PlayerStat], lose_team : List[PlayerStat]):
        raw_result : List[Tuple[Rating]] = \
            self.env.rate([tuple(i.rating for i in win_team), tuple(i.rating for i in lose_team)])
        for team, result in zip([win_team, lose_team], raw_result):
            for pl, pl_result in zip(team, result):
                if team is win_team:
                    pl.win += 1
                else:
                    pl.lose += 1
                pl.rating = pl_result
                self.player_cache[pl.discord_id] = pl

    def run(self):
        matchs = db.get_all_matchs()
        print(f"Total match: {len(matchs)}")
        for i, match in enumerate(matchs):
            print(i, match.id)
            if match.report.gametype != GameType.TEAMER:
                continue
            players = match.report.players
            win_team = [self.get_player(i.id) for i in players if i.position == 1]
            lose_team = [self.get_player(i.id) for i in players if i.position != 1]
            if not win_team or not lose_team:
                continue
            self.rate_teamer(win_team, lose_team)

        players = list(self.player_cache.values())
        players.sort(key=lambda playerStat: playerStat.elden, reverse=True)
        print(*[f"``#{i+1}: elden: {int(pl.elden)} ts: {int(pl.rating.mu)} RD: {int(pl.rating.sigma)}`` <@{pl.discord_id}> ({pl.win}/{pl.lose})"
                for i, pl in enumerate(players[:100])], sep='\n')