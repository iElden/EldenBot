import sqlite3 as sq3
import json
import nextcord
from typing import Optional, Tuple
from enum import IntEnum

from .ReportParser import Report, GameType
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
        json TEXT)
        """)
        self.conn.commit()

    def get_s1_match(self) -> ...:
        data = self.conn.execute("SELECT id, validated, json FROM RankedMatchs WHERE id = ?", (match_id,))
        rt = data.fetchone()
        if not rt:
            return None
        return ...

    def add_s1_match(self, ranked_match):
        ...

    def valid_s1_match(self, ranked_match):
        ranked_match.validated = True
        self.conn.execute('UPDATE RankedMatchs SET validated = 1 WHERE id = ?',
                          (match.id,))
        self.conn.commit()

    def unvalid_s1_match(self, ranked_match):
        ranked_match.validated = False
        self.conn.execute('UPDATE RankedMatchs SET validated = 0 WHERE id = ?',
                          (match.id,))
        self.conn.commit()

    def get_s1_player_stats(self, player_id) -> ...:
        return ...

    def update_s1_player_stats(self, player_stat):
        ...

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

    def get_all_players(self):
        data = self.conn.execute("SELECT discord_id FROM Players")  # execute a simple SQL select query
        players = data.fetchall()  # get all the results from the above query
        return [i[0] for i in players]

db = Database()
db.create_tables()
