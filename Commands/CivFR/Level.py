import sqlite3 as sq3
from typing import List, Set

from util.function import get_member, list_to_block
from util.exception import Forbidden, InvalidArgs, NotFound
from .utils import is_arbitre

ROLE = {
    "10": 754681667037429840,
    "20FFA": 754681661425451058,
    "20Teamer": 754681664629899375,
    "25": 754685865292333087,
    "30": 754681648917774458
}

OBSOLETE_ROLES = {
    "10": [],
    "20FFA": [],
    "20Teamer": ["10"],
    "25": ["20Teamer", "20FFA"],
    "30": ["25"]
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

class Requirement:
    @classmethod
    def get_role_for(cls, player_stat : PlayerStat) -> List[str]:
        roles = [s for s, func in cls.ROLE_REQUIREMENT.items() if func(cls, player_stat)]
        for i in cls._recursive_get_obsolete_roles(roles):
            if i in roles:
                roles.remove(i)
        return roles

    @classmethod
    def _recursive_get_obsolete_roles(cls, roles) -> Set[str]:
        rt = set()
        for role in roles:
            rt = rt.union(set(OBSOLETE_ROLES[role]))
            rt = rt.union(cls._recursive_get_obsolete_roles(OBSOLETE_ROLES[role]))
        return rt

        @classmethod
        def level_10(cls, player_stat : PlayerStat) -> bool:
            return player_stat.begin_ffa_play >= 10

        @classmethod
        def level_20_ffa(cls, player_stat : PlayerStat) -> bool:
            return player_stat.begin_ffa_win >= 10

        @classmethod
        def level_20_teamer(cls, player_stat : PlayerStat) -> bool:
            return player_stat.begin_teamer_win >= 10

        @classmethod
        def level_25(cls, player_stat : PlayerStat) -> bool:
            return player_stat.teamer_win >= 20 or player_stat.ffa_win >= 5 or player_stat.great_player

        @classmethod
        def level_30(cls, player_stat : PlayerStat) -> bool:
            return cls.level_25(player_stat) and not player_stat.is_bad_coatch

    ROLE_REQUIREMENT = {
        "10": level_10.__func__,
        "20FFA": level_20_ffa.__func__,
        "20Teamer": level_20_teamer.__func__,
        "25": level_25.__func__,
        "30": level_30.__func__
    }

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

async def recalc_role_for(member):
    debug_msg = ["+ [DEBUG]"]
    player_stat = db.get_stat_for(member.id)
    new_lvl_roles = Requirement.get_role_for(player_stat)
    new_lvl_roles_id = set(ROLE[i] for i in new_lvl_roles)
    debug_msg.append(f"= {member} is eligible for roles : {new_lvl_roles} ({new_lvl_roles_id})")
    old_lvl_roles_id = set(i.id for i in member.roles if i.id in ROLE.values())
    debug_msg.append(f"= {member} curently have lvl roles ID: {old_lvl_roles_id}")
    if old_lvl_roles_id != new_lvl_roles_id:
        debug_msg.append(f"- {member} Roles are different, updating ...")
        if old_lvl_roles_id:
            debug_msg.append(f"+ removing all lvl roles")
            await member.remove_roles(*(member.guild.get_role(i) for i in old_lvl_roles_id))
        debug_msg.append(f"+ giving new lvl roles")
        print(new_lvl_roles)
        await member.add_roles(*(member.guild.get_role(ROLE[i]) for i in new_lvl_roles))
    return debug_msg


class CmdCivFRLevel:
    async def cmd_getstats(self, *args, member, channel, guild, **_):
        if not args:
            target = member
        else:
            name = ' '.join(args)
            target = get_member(guild, name)
            if not target:
                raise NotFound(f"Member named \"{name}\" not found")
        pl = db.get_stat_for(target.id)
        await channel.send(str(pl))

    async def cmd_setcivfr(self, *args, member, guild, channel, force, **_):
        if not is_arbitre(member) and not force:
            raise Forbidden("You must be Arbitre for use this command")
        member = guild.get_member(int(args[0]))
        if not member:
            raise NotFound(f"Member {args[0]} not found")
        db.manual_query_set(*args)
        await channel.send("Stats changed")
        dbg = await recalc_role_for(member)
        await channel.send(list_to_block(dbg))
