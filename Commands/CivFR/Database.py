import sqlite3 as sq3
import json
import discord
from typing import Optional, Tuple

from .ReportParser import Report, GameType
from util.exception import InvalidArgs

GAMETYPE_TO_LOWERCASE = {
    GameType.BEGIN_FFA: "begin_ffa",
    GameType.FFA: "ffa",
    GameType.BEGIN_TEAMER: "begin_teamer",
    GameType.TEAMER: "teamer"
}

class PlayerStat:
    def __init__(self, discord_id, level, ffa_play, ffa_win, teamer_play, teamer_win,
                 begin_ffa_play, begin_ffa_win, begin_teamer_play, begin_teamer_win, great_player, is_bad_coatch):
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

    def __str__(self):
        return (f"FFA win: {self.ffa_win}\nFFA play: {self.ffa_play}\n"
                f"Teamer win: {self.teamer_win}\nTeamer play: {self.teamer_play}\n\n"
                f"Begin FFA win: {self.begin_ffa_win}\nBegin FFA play: {self.begin_ffa_play}\n"
                f"Begin Teamer win: {self.begin_teamer_win}\nBegin Teamer play: {self.begin_teamer_play}\n\n"
                f"Great Player: {self.great_player}\nIs bad coatch: {self.is_bad_coatch}")

class Match:
    def __init__(self, match_id, validated, report, check_msg_id=None):
        self.id : int = match_id
        self.check_msg_id: Optional[int] = check_msg_id
        self.validated : bool = validated
        self.report : Report = report

    def to_embed(self) -> discord.Embed:
        colour, txt = self.get_warning()
        em = discord.Embed(title="ReportParser",
                           description=f"Gametype : {self.report.gametype.value}\n\n{self.report.players_to_strings()}",
                           color=colour)
        if txt:
            em.add_field(name="Status", value=txt)
        return em

    def get_warning(self) -> Tuple[int, Optional[str]]:
        if self.validated:
            return 0x3498DB, "Report validé"
        if not self.report or not self.report.players:
            return 0xE74C3C, "Le report ne contient aucun joueur"
        if not self.report.gametype:
            return 0xE74C3C, "Le report ne contient pas le type de partie ou ce dernier n'est pas reconnu"
        if not all(i.is_valid() for i in self.report.players):
            return 0xF1C40F, "Certain joueur possède des données invalides"
        if len(self.report.players) < 4:
            return 0xF1C40F, "Le report contient un nombre de joueur suspect"
        return 0x2ECC71, "En attente de validation"


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
        is_bad_coatch BOOLEAN NOT NULL DEFAULT 0)
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS Matchs
        (id INT PRIMARY KEY,
        check_msg_id INT,
        validated BOOLEAN NOT NULL DEFAULT 0,
        json TEXT)
        """)
        self.conn.commit()

    def get_stat_for(self, discord_id) -> PlayerStat:
        data = self.conn.execute("""
            SELECT level, ffa_play, ffa_win, teamer_play, teamer_win, begin_ffa_play, begin_ffa_win, begin_teamer_play, begin_teamer_win, great_player, is_bad_coatch
            FROM Players WHERE discord_id = ?""", (discord_id,))
        rt = data.fetchone()
        if not rt:
            return PlayerStat(discord_id, *[0]*11)
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


db = Database()
db.create_tables()