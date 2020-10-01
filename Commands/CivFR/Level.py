from typing import List, Set
import discord
import asyncio

from util.function import get_member, list_to_block
from util.exception import Forbidden, InvalidArgs, NotFound, ALEDException
from .utils import is_arbitre
from .ReportParser import Report, GameType
from .constant import CIVFR_GUILD_ID, TURKEY

from .Database import db, PlayerStat, Match

ROLE = {
    "10": 754681667037429840,
    "20FFA": 754681661425451058,
    "20Teamer": 754681664629899375,
    "25": 754685865292333087,
    "30": 754681648917774458
}

REPORT_CHANNEL = 754874164447412305
OBSOLETE_ROLES = {
    "10": [],
    "20FFA": [],
    "20Teamer": ["10"],
    "25": ["20Teamer", "20FFA"],
    "30": ["25"]
}

POSITION_REQUIRE_FOR_WIN = {
    GameType.BEGIN_FFA : 2,
    GameType.BEGIN_TEAMER : 1,
    GameType.FFA : 1,
    GameType.TEAMER : 1
}

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
        return player_stat.begin_ffa_win >= 10 or player_stat.great_player

    @classmethod
    def level_20_teamer(cls, player_stat : PlayerStat) -> bool:
        return player_stat.begin_teamer_win >= 10 or player_stat.great_player

    @classmethod
    def level_25(cls, player_stat : PlayerStat) -> bool:
        return player_stat.teamer_win >= 20 or player_stat.ffa_win >= 5

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

async def on_message(message):
    if message.channel.id != REPORT_CHANNEL:
        return
    if not message.content.lower().startswith("game"):
        return
    report = Report.from_str(message.content)
    match = Match(message.id, False, report)
    validation_msg = await message.channel.send(embed=match.to_embed())
    match.check_msg_id = validation_msg.id
    db.add_match(match)
    await validation_msg.add_reaction(TURKEY)

async def on_reaction(payload : discord.RawReactionActionEvent, *, client : discord.Client):
    if payload.channel_id != REPORT_CHANNEL or str(payload.emoji) != TURKEY :
        return
    civfr : discord.Guild = client.get_guild(CIVFR_GUILD_ID)
    member : discord.Member = civfr.get_member(payload.user_id)
    if not member:
        raise ALEDException("Member not found on CivFR")
    if not is_arbitre(member):
        return
    match = db.get_match(payload.message_id)
    if not match or match.validated:
        return
    db.valid_match(match)
    # update Players Stats database
    for i in match.report.players:
        db.register_plstats(i.id,
                            match.report.gametype,
                            i.position <= POSITION_REQUIRE_FOR_WIN[match.report.gametype])
    # Verif if players are eligible to new roles
    tasks = [recalc_role_for(civfr.get_member(i.id)) for i in match.report.players]
    rt = await asyncio.gather(*tasks)
    # Change embed
    validation_msg = await client.get_channel(payload.channel_id).fetch_message(match.check_msg_id)
    await validation_msg.edit(embed=match.to_embed())
    await validation_msg.clear_reactions()

async def on_edit(payload : discord.RawMessageUpdateEvent, client):
    if payload.channel_id != REPORT_CHANNEL:
        return
    match = db.get_match(payload.message_id)
    if not match or match.validated or match.id != payload.message_id:
        return
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    report = Report.from_str(message.content)
    new_match = Match(message.id, False, report, match.check_msg_id)
    validation_msg = await client.get_channel(payload.channel_id).fetch_message(match.check_msg_id)
    await validation_msg.edit(embed=new_match.to_embed())
    db.add_match(new_match) # add_match use "INSERT OR UPDATE" SQL

async def on_delete(payload : discord.RawMessageDeleteEvent, client):
    if payload.channel_id != REPORT_CHANNEL:
        return
    match = db.get_match(payload.message_id)
    if not match or match.validated:
        return
    validation_msg = await client.get_channel(payload.channel_id).fetch_message(match.check_msg_id)
    await validation_msg.delete()
    db.remove_match(match)


async def recalc_role_for(member):
    if not member:
        return
    player_stat = db.get_stat_for(member.id)
    new_lvl_roles = Requirement.get_role_for(player_stat)
    new_lvl_roles_id = set(ROLE[i] for i in new_lvl_roles)
    old_lvl_roles_id = set(i.id for i in member.roles if i.id in ROLE.values())
    if old_lvl_roles_id != new_lvl_roles_id:
        if old_lvl_roles_id:
            await member.remove_roles(*(member.guild.get_role(i) for i in old_lvl_roles_id))
        await member.add_roles(*(member.guild.get_role(ROLE[i]) for i in new_lvl_roles))


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
