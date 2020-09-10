import sqlite3 as sq3

from util.function import get_member
from util.exception import Forbidden, InvalidArgs, NotFound
from .utils import is_arbitre

class PlayerStat:
    def __init__(self, discord_id, level, ffa_play, ffa_win, teamer_play, teamer_win, great_player, is_bad_coatch):
        self.discord_id : int = discord_id
        self.level : int = level
        self.ffa_play : int = ffa_play
        self.ffa_win : int = ffa_win
        self.teamer_play : int = teamer_play
        self.teamer_win : int = teamer_win
        self.great_player : bool = great_player
        self.is_bad_coatch : bool = is_bad_coatch

class Database:

    def __init__(self):
        self.conn = sq3.connect("data/civfr.db")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS Players
        (discord_id INT PRIMARY KEY,
        level INT NOT NULL DEFAULT 0,
        ffa_play INT NOT NULL DEFAULT 0 ,
        ffa_win INT NOT NULL DEFAULT 0 ,
        teamer_play INT NOT NULL DEFAULT 0,
        teamer_win INT NOT NULL DEFAULT 0,
        great_player BOOLEAN NOT NULL DEFAULT 0,
        is_bad_coatch BOOLEAN NOT NULL DEFAULT 0)
        """)
        self.conn.commit()

    def get_stat_for(self, discord_id) -> PlayerStat:
        data = self.conn.execute("""
            SELECT level, ffa_play, ffa_win, teamer_play, teamer_win, great_player, is_bad_coatch
            FROM Players WHERE discord_id = ?""", (discord_id,))
        rt = data.fetchone()
        if not rt:
            return PlayerStat(discord_id, 0, 0, 0, 0, 0, 0, 0)
        return PlayerStat(discord_id, *rt[0])

    def manual_query_set(self, *args):
        if len(args) != 3:
            raise InvalidArgs("Args must be the discord_id, key and the value")
        self.set(args[1], args[2], args[0])

    def set(self, discord_id, key, value, create=True):
        if create:
            self.conn.execute("INSERT OR IGNORE INTO Players(discord_id) VALUES (?)", (discord_id,))
        self.conn.execute("UPDATE Players SET ? = ? WHERE discord_id = ?", (discord_id, key, value))
        self.conn.commit()

    def register_ffa(self, discord_id, win=False):
        pl = self.get_stat_for(discord_id)
        self.set(discord_id, f"ffa_play", pl.ffa_play + 1)
        if win:
            self.set(discord_id, f"ffa_win", pl.ffa_win + 1, create=False)

    def register_teamer(self, discord_id, win=False):
        pl = self.get_stat_for(discord_id)
        self.set(discord_id, f"teamer_play", pl.teamer_play + 1)
        if win:
            self.set(discord_id, f"teamer_win", pl.teamer_win + 1, create=False)

db = Database()

class CmdCivFRLevel:

    async def cmd_getstats(self, *args, member, channel, guild):
        if not args:
            target = member
        else:
            name = ' '.join(args)
            target = get_member(guild, name)
            if not target:
                raise NotFound(f"Member named \"{name}\" not found")
        pl = db.get_stat_for(target.id)
        await channel.send(f"Level: {pl.level}\nFFA win: {pl.ffa_win}\nFFA play: {pl.ffa_play}\nTeamer win: {pl.teamer_win}\nTeamer play: {pl.teamer_play}\nGreat Player: {pl.great_player}\nIs bad coatch: {pl.is_bad_coatch}")

    async def cmd_setcivfr(self, *args, member, channel, force):
        if not is_arbitre(member) and not force:
            raise Forbidden("You must be Arbitre for use this command")
        db.manual_query_set(*args)
        await channel.send("Stats changed")