import random
import sqlite3 as sq3
import json
import nextcord
from typing import Optional, Tuple, List, Dict
from enum import IntEnum
from trueskill import Rating

from .ReportParser import Report, GameType
from .constant import RANKED_CHANNEL, RANKED_ADMIN_ROLES, RANKED_ADMIN_USERS, MU, SIGMA, SKILL
from util.exception import InvalidArgs

GAMETYPE_TO_LOWERCASE = {
    GameType.BEGIN_FFA: "begin_ffa",
    GameType.FFA: "ffa",
    GameType.BEGIN_TEAMER: "begin_teamer",
    GameType.TEAMER: "teamer"
}

class Color(IntEnum):
    BLUE = 0x3498DB
    GREEN = 0x2ECC71
    YELLOW = 0xF1C40F
    RED = 0xE74C3C
    PURPLE = 0x9B59B6

class PlayerStat:
    def __init__(self, discord_id, level, ffa_play, ffa_win, teamer_play, teamer_win, begin_ffa_play, begin_ffa_win,
                 begin_teamer_play, begin_teamer_win, great_player, is_bad_coatch, longdate_member):
        self.discord_id : int = discord_id
        self.level : int = level
        self.ffa_play : int = ffa_play
        self.ffa_win : int = ffa_win
        self.teamer_play : int = teamer_play
        self.teamer_win : int = teamer_win
        self.begin_ffa_play : int = begin_ffa_play
        self.begin_ffa_win : int = begin_ffa_win
        self.begin_teamer_play : int = begin_teamer_play
        self.begin_teamer_win : int = begin_teamer_win
        self.great_player : bool = great_player
        self.is_bad_coatch : bool = is_bad_coatch
        self.longdate_member : bool = longdate_member

    def __str__(self):
        return (f"FFA win: {self.ffa_win}\nFFA play: {self.ffa_play}\n"
                f"Teamer win: {self.teamer_win}\nTeamer play: {self.teamer_play}\n\n"
                f"Begin FFA win: {self.begin_ffa_win}\nBegin FFA play: {self.begin_ffa_play}\n"
                f"Begin Teamer win: {self.begin_teamer_win}\nBegin Teamer play: {self.begin_teamer_play}\n\n"
                f"Great Player: {self.great_player}\nIs bad coatch: {self.is_bad_coatch}\nLongtime Player: {self.longdate_member}")

class ReportStatus:
    def __init__(self,color, text, is_valid):
        self.color = color
        self.text = text
        self.is_valid = is_valid

class Match:
    def __init__(self, match_id, validated, report, check_msg_id=None):
        self.id : int = match_id
        self.check_msg_id: Optional[int] = check_msg_id
        self.validated : bool = validated
        self.report : Report = report

    def to_embed(self, author_id : Optional[int]=None) -> nextcord.Embed:
        colour, txt = self.get_warning(author_id)
        em = nextcord.Embed(title="ReportParser",
                           description=f"Gametype : {self.report.gametype and self.report.gametype.value}\n\n{self.report.players_to_strings()}",
                           color=colour.value)
        if txt:
            em.add_field(name="Status", value=txt)
        return em

    def get_warning(self, author_id : Optional[int]) -> Tuple[Color, Optional[str]]:
        color, string = self._get_warning()
        if self.validated:
            if author_id and color == Color.GREEN:
                return Color.BLUE, f"Report validé par <@{author_id}>"
            elif author_id:
                return Color.PURPLE, f"Report validé par <@{author_id}> MAIS\n{string}"
            elif color == Color.GREEN:
                return Color.BLUE, f"Report validé"
            else:
                return Color.PURPLE, f"Report validé MAIS\n{string}"
        return color, string

    def _get_warning(self) -> Tuple[Color, Optional[str]]:
        if not self.report:
            return Color.RED, "Le parsing du report à complètement foiré"
        if not self.report.gametype:
            return Color.RED, "Le report ne contient pas le type de partie ou ce dernier n'est pas reconnu"
        if not self.report.players:
            return Color.RED, "Aucun joueur n'est présent dans le report"
        if not all(i.is_valid() for i in self.report.players):
            return Color.YELLOW, "Certains joueurs possèdent des données invalides"
        if len(self.report.players) < 6:
            return Color.YELLOW, "Le report contient un nombre de joueurs suspect"
        if (self.report.gametype in [GameType.BEGIN_TEAMER, GameType.TEAMER] and
            len([i for i in self.report.players if i.position == 1]) != len([i for i in self.report.players if i.position == 2])):
            return Color.YELLOW, "Les équipes ne contienne pas le même nombre de joueur"
        if self.report.gametype in [GameType.BEGIN_TEAMER, GameType.TEAMER] and any([i for i in self.report.players if i.position not in [1, 2]]):
            return Color.YELLOW, "Les équipes ne contienne pas le même nombre de joueur"
        return Color.GREEN, "En attente de validation"

class RankedStats2:
    def __init__(self, discord_id, mu, sigma, games, wins, first):
        self.id = discord_id
        self.mu = mu
        self.sigma = sigma
        self.games = games
        self.wins = wins
        self.first = first

    def get_rating(self):
        return Rating(self.mu, self.sigma)

    def create_embed_field(self, em : nextcord.Embed):
        statlist: List[Tuple[str, ...]] = [
            ('Points', f"{SKILL(self.get_rating()):.0f}"),
            ('TS Mu', f"{self.mu:.0f}"),
            ('TS Sigma', f"{self.sigma:.0f}"),
            # ('Win %', f'{self.wins / self.games:.1%}'),
            ('Partie jouées', f"{self.games}"),
            ('Victoire', f"{self.wins}"),
            ('Premier', f"{self.first}"),
            ('✅ Café bu', self.id if self.id in RANKED_ADMIN_USERS else 0)
        ]
        max_length = max(len(i) for i, _ in statlist)
        em.add_field(name='FFA Ranked', value='\n'.join(f"`{i:>{max_length}}`: {j}" for i, j in statlist))

    def to_embed(self, member=None):
        em = nextcord.Embed(title="Stats classées", description=f"Stat de <@{self.id}>", colour=member.colour if member else 0)
        self.create_embed_field(em)
        return em

class RankedMatch:

    import Commands.CivFR.Ranked.RankCalculator as RankCalculator

    def __init__(self, players_pos : Dict[int, int], validated=False, match_id=None, scrapped=False):
        self.players : List[int] = [i for i in players_pos.keys()]
        self.players_pos : Dict[int, int] = players_pos # {player_id: position}
        self.validated : bool = validated
        self.scrapped : bool = scrapped
        self.id : Optional[int] = match_id

        self.report_status = self.get_report_status()

    @classmethod
    def new_game(cls, players : List[int]):
        self = cls({k: None for k in players})
        return self

    async def delete(self, client : nextcord.Client):
        channel = client.get_channel(RANKED_CHANNEL)
        msg : nextcord.PartialMessage = channel.get_partial_message(self.id)
        await msg.delete()

    async def update_embed(self, client : nextcord.Client):
        channel = client.get_channel(RANKED_CHANNEL)
        msg : nextcord.PartialMessage = channel.get_partial_message(self.id)
        await msg.edit(embed=self.get_embed())

    def _get_embed_desc(self) -> str:
        desc = ""
        if self.report_status.is_valid:
            player_ranks : Dict[int, float] = self.RankCalculator.RankPreviewer.get_ranks_preview(self)
            if self.scrapped:
                for pl in sorted(self.players):
                    desc += f"\n``[{player_ranks[pl]:+4.0f}] -:`` <@{pl}>"
                return desc
            # if game not scrapped :
            for pl, pos in sorted(self.players_pos.items(), key=lambda x: x[1]):
                desc += f"\n``[{player_ranks[pl]:+4.0f}] {pos:>2}:`` <@{pl}>"
        else:
            for i in range(1, len(self.players)+1):
                desc += f"\n``{i:>2}:``" + ' ,'.join(f"<@{pl}>" for pl in self.players if self.players_pos[pl] == i)
            pl_waiting = [k for k, v in self.players_pos.items() if v is None]
            if pl_waiting:
                desc += "\n\nEn attente de pointage: " + ', '.join(f"<@{pl}>" for pl in pl_waiting)
        return desc

    def get_embed(self) -> nextcord.Embed:
        self.report_status = self.get_report_status()
        desc = self._get_embed_desc()
        em = nextcord.Embed(title="Ranked Report", description=desc, colour=self.report_status.color)
        em.add_field(name="Status", value=self.report_status.text)
        return em

    def get_report_status(self) -> ReportStatus:
        if self.scrapped:
            return ReportStatus(Color.PURPLE,
                                "Match scrap",
                                True)
        if self.validated:
            return ReportStatus(Color.BLUE,
                                "Match validé",
                                True)
        if None in self.players_pos.values():
            return ReportStatus(Color.RED,
                                "Un ou plusieur joueurs n'ont pas validé leur position.\nLes joueurs qui n'ont pas validé leur position avant 24h seront placés derniers.",
                                False)
        if len(set(self.players_pos.values())) != len(self.players):
            return ReportStatus(Color.YELLOW,
                                "Les Ties ne sont pas autorisés sur CivFR.",
                                False)
        return ReportStatus(Color.GREEN,
                            "En attente d'une validation par un Administrateur: " + ''.join(f"<@&{i}>" for i in RANKED_ADMIN_ROLES) + ''.join(f"<@{i}>" for i in RANKED_ADMIN_USERS),
                            True)


    def set_player_position(self, player_id : int, position : int):
        self.players_pos[player_id] = position

    def fill_unreported_players(self, author : nextcord.User) -> str:
        old_str = self.player_pos_oneliner()
        pl_pos = sorted(self.players_pos.items(), key=lambda i: i[1] if i[1] is not None else 99)
        good_players = [k for k, v in pl_pos if v is not None]
        bad_players = [k for k, v in pl_pos if v is None]
        random.shuffle(bad_players)
        self.players_pos = {pl: pos+1 for pos, pl in enumerate(good_players + bad_players)}
        new_str = self.player_pos_oneliner()
        bad_players_str = ' '.join(f"<@{i}>" for i in bad_players)
        return (f"{author.mention} has requested autofill for match {self.id}. targetting : {bad_players_str}\n"
                f"Old: {old_str}\nNew: {new_str}")

    def player_pos_oneliner(self) -> str:
        ls = sorted(self.players_pos.items(), key=lambda i: i[1] if i[1] is not None else 99)
        return ', '.join(f"{'?' if None else pos}: <@{pl}>" for pl, pos in ls)

    def get_players_mention_string(self) -> str:
        return ' '.join(f"<@{i}>" for i in self.players)

    @classmethod
    def from_db(cls, js, validated, match_id):
        return cls({int(k):v for k, v in js.items()}, validated, match_id)

class Database:
    def __init__(self):
        self.conn = sq3.connect("data/civfr.db")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS Players
        (discord_id INT PRIMARY KEY,
        level INT NOT NULL DEFAULT 0,
        ffa_play INT NOT NULL DEFAULT 0,
        ffa_win INT NOT NULL DEFAULT 0,
        teamer_play INT NOT NULL DEFAULT 0,
        teamer_win INT NOT NULL DEFAULT 0,
        begin_ffa_play INT NOT NULL DEFAULT 0,
        begin_ffa_win INT NOT NULL DEFAULT 0,
        begin_teamer_play INT NOT NULL DEFAULT 0,
        begin_teamer_win INT NOT NULL DEFAULT 0,
        great_player BOOLEAN NOT NULL DEFAULT 0,
        is_bad_coatch BOOLEAN NOT NULL DEFAULT 0,
        longdate_member BOOLEAN NOT NULL DEFAULT 0)
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS Matchs
        (id INT PRIMARY KEY,
        check_msg_id INT,
        validated BOOLEAN NOT NULL DEFAULT 0,
        json TEXT)
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS RankedMatchs
        (id INT PRIMARY KEY,
        validated BOOLEAN NOT NULL DEFAULT 0,
        scrapped BOLLEAN NOT NULL DEFAULT 0,
        validator_id INT,
        json TEXT)
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS RankedStats2
        (id INT PRIMARY KEY NOT NULL,
        mu INT NOT NULL DEFAULT 0,
        sigma INT NOT NULL DEFAULT 0,
        games INT NOT NULL DEFAULT 0,
        wins INT NOT NULL DEFAULT 0,
        first INT NOT NULL DEFAULT 0)
        """)
        self.conn.commit()

    def get_s1_match(self, match_id) -> Optional[RankedMatch]:
        data = self.conn.execute("SELECT id, validated, json FROM RankedMatchs WHERE id = ?", (match_id,))
        rt = data.fetchone()
        if not rt:
            return None
        return RankedMatch.from_db(json.loads(rt[2]), rt[1], rt[0])

    def add_s1_match(self, ranked_match : RankedMatch):
        js = json.dumps(ranked_match.players_pos)
        self.conn.execute("INSERT OR REPLACE INTO RankedMatchs (id, validated, json) VALUES (?, ?, ?)",
                          (ranked_match.id, ranked_match.validated, js))
        self.conn.commit()

    def update_s1_match(self, ranked_match : RankedMatch):
        js = json.dumps(ranked_match.players_pos)
        self.conn.execute("UPDATE RankedMatchs SET validated=?, json=? WHERE id=?",
                          (ranked_match.validated, js, ranked_match.id))
        self.conn.commit()

    def valid_s1_match(self, ranked_match):
        ranked_match.validated = True
        self.conn.execute('UPDATE RankedMatchs SET validated = 1 WHERE id = ?',(ranked_match.id,))
        self.conn.commit()

    def unvalid_s1_match(self, ranked_match):
        ranked_match.validated = False
        self.conn.execute('UPDATE RankedMatchs SET validated = 0 WHERE id = ?',(ranked_match.id,))
        self.conn.commit()

    def scrap_s1_match(self, ranked_match):
        ranked_match.scrapped = True
        for pl in ranked_match.players:
            ranked_match.set_player_position(pl, 0)
        js = json.dumps(ranked_match.players_pos)
        self.conn.execute('UPDATE RankedMatchs SET scrapped=1, validated=1, json=? WHERE id = ?', (js, ranked_match.id))
        self.conn.commit()

    def delete_s1_match(self, ranked_match):
        self.conn.execute('DELETE FROM RankedMatchs WHERE id = ?', (ranked_match.id,))
        self.conn.commit()

    def get_s1_player_stats(self, player_id) -> RankedStats2:
        data = self.conn.execute("SELECT * FROM RankedStats2 WHERE id = ?", (player_id,))
        rt = data.fetchone()
        if not rt:
            return RankedStats2(player_id, MU, SIGMA, 0, 0, 0)
        return RankedStats2(*rt)

    def update_s1_player_stats(self, rs : RankedStats2):
        self.conn.execute("INSERT OR REPLACE INTO RankedStats2(id, mu, sigma, games, wins, first) VALUES (?,?,?,?,?,?)",
                          (rs.id, rs.mu, rs.sigma, rs.games, rs.wins, rs.first))
        self.conn.commit()

    def get_all_s1_players_stats(self, min_games=1) -> List[RankedStats2]:
        data = self.conn.execute("SELECT * FROM RankedStats2 WHERE games >= ?", (min_games,))
        rts = data.fetchall()
        return [RankedStats2(*rt) for rt in rts]

    def get_stat_for(self, discord_id) -> PlayerStat:
        data = self.conn.execute("""
            SELECT level, ffa_play, ffa_win, teamer_play, teamer_win, begin_ffa_play, begin_ffa_win, begin_teamer_play, begin_teamer_win, great_player, is_bad_coatch, longdate_member
            FROM Players WHERE discord_id = ?""", (discord_id,))
        rt = data.fetchone()
        if not rt:
            return PlayerStat(discord_id, *[0]*12)
        return PlayerStat(discord_id, *rt)

    def manual_query_set(self, *args):
        if len(args) != 3:
            raise InvalidArgs("Args must be the discord_id, key and the value")
        self.set(args[0], args[1], args[2])

    def set(self, discord_id, key, value, create=True):
        if create:
            self.conn.execute("INSERT OR IGNORE INTO Players(discord_id) VALUES (?)", (discord_id,))
        self.conn.execute('UPDATE Players SET "{}" = ? WHERE discord_id = ?'.format(key.replace('"', '""')), (value, discord_id))
        self.conn.commit()

    def register_plstats(self, discord_id : int, gameType : GameType, win : bool=False):
        txt = GAMETYPE_TO_LOWERCASE[gameType]
        pl = self.get_stat_for(discord_id)
        self.set(discord_id, f"{txt}_play", getattr(pl, f"{txt}_play") + 1)
        if win:
            self.set(discord_id, f"{txt}_win", getattr(pl, f"{txt}_win") + 1, create=False)

    def unregister_plstats(self, discord_id : int, gameType : GameType, win : bool=False):
        txt = GAMETYPE_TO_LOWERCASE[gameType]
        pl = self.get_stat_for(discord_id)
        self.set(discord_id, f"{txt}_play", getattr(pl, f"{txt}_play") - 1)
        if win:
            self.set(discord_id, f"{txt}_win", getattr(pl, f"{txt}_win") - 1, create=False)

    def add_match(self, match : Match):
        js = json.dumps(match.report.to_json())
        self.conn.execute("INSERT OR REPLACE INTO Matchs (id, check_msg_id, validated, json) VALUES (?, ?, ?, ?)",
                          (match.id, match.check_msg_id, match.validated, js))
        self.conn.commit()

    def valid_match(self, match : Match):
        match.validated = True
        self.conn.execute('UPDATE Matchs SET validated = 1 WHERE id = ?',
                          (match.id,))
        self.conn.commit()

    def unvalid_match(self, match : Match):
        match.validated = True
        self.conn.execute('UPDATE Matchs SET validated = 0 WHERE id = ?',
                          (match.id,))
        self.conn.commit()

    def remove_match(self, match_id : int):
        self.conn.execute('DELETE FROM Matchs WHERE id = ?',
                          (match_id,))
        self.conn.commit()

    def delete_all_current_stats(self):
        self.conn.execute('DELETE FROM RankedStats2')
        self.conn.commit()

    def get_match(self, match_id : int) -> Optional[Match]:
        data = self.conn.execute("SELECT id, check_msg_id, validated, json FROM Matchs WHERE id = ? OR check_msg_id = ?", (match_id, match_id))
        rt = data.fetchone()
        if not rt:
            return None
        js = json.loads(rt[3])
        return Match(int(rt[0]), bool(rt[2]), Report.from_json(js), rt[1] and int(rt[1]))

    def get_all_matchs(self):
        data = self.conn.execute("SELECT id, check_msg_id, validated, json FROM Matchs WHERE Validated = 1")
        rts = data.fetchall()
        return [Match(int(rt[0]), bool(rt[2]), Report.from_json(json.loads(rt[3])), rt[1] and int(rt[1])) for rt in rts]

    def get_all_ranked_matchs_from(self, start_id : str) -> List[RankedMatch]:
        data = self.conn.execute(f"SELECT id, validated, json FROM RankedMatchs WHERE id>{start_id} AND validated=1")
        rts = data.fetchall()
        return [RankedMatch.from_db(json.loads(rt[2]), rt[1], rt[0]) for rt in rts]

    def get_all_players(self):
        data = self.conn.execute("SELECT discord_id FROM Players")  # execute a simple SQL select query
        players = data.fetchall()  # get all the results from the above query
        return [i[0] for i in players]

db : Database = Database()
db.create_tables()
