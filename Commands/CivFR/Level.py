from typing import List, Set, Optional
import discord
import asyncio

from util.function import get_member
from util.exception import Forbidden, InvalidArgs, NotFound, ALEDException, BotError
from util.decorator import only_owner
from .utils import is_arbitre, is_civfr_guild_or_mp
from .ReportParser import Report, GameType
from .constant import CIVFR_GUILD_ID, TURKEY

from .Database import db, PlayerStat, Match

ROLE = {
    "10": 754681667037429840,
    "15FFA": 777882591500042272,
    "15Teamer": 770361077224964178,
    "20FFA": 754681661425451058,
    "20Teamer": 754681664629899375,
    "25": 754685865292333087,
    "30": 754681648917774458
}

REPORT_CHANNEL = 761277487057469460
OBSOLETE_ROLES = {
    "10": [],
    "15FFA": [],
    "15Teamer": ["10"],
    "20FFA": ["15FFA"],
    "20Teamer": ["15Teamer"],
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
        return player_stat.begin_ffa_play >= 10 or player_stat.longdate_member

    @classmethod
    def level_15_ffa(cls, player_stat : PlayerStat) -> bool:
        return player_stat.begin_ffa_win >= 10 or player_stat.great_player

    @classmethod
    def level_15_teamer(cls, player_stat : PlayerStat) -> bool:
        return player_stat.begin_teamer_win >= 10 or player_stat.great_player

    @classmethod
    def level_20_ffa(cls, player_stat : PlayerStat) -> bool:
        return player_stat.begin_ffa_win >= 60

    @classmethod
    def level_20_teamer(cls, player_stat : PlayerStat) -> bool:
        return player_stat.teamer_win >= 10 or player_stat.begin_teamer_win >= 60

    @classmethod
    def level_25(cls, player_stat : PlayerStat) -> bool:
        return player_stat.teamer_win >= 20 or player_stat.ffa_win >= 5

    @classmethod
    def level_30(cls, player_stat : PlayerStat) -> bool:
        return cls.level_25(player_stat) and not player_stat.is_bad_coatch

    ROLE_REQUIREMENT = {
        "10": level_10.__func__,
        "15FFA": level_15_ffa.__func__,
        "15Teamer": level_15_teamer.__func__,
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
    civfr: discord.Guild = client.get_guild(CIVFR_GUILD_ID)
    member : discord.Member = civfr.get_member(payload.user_id)
    if not member:
        raise ALEDException("Member not found on CivFR")
    if not is_arbitre(member, client=client):
        return
    await valid_report(payload.message_id, payload.channel_id, civfr, client, member.id)

async def valid_report(message_id, channel_id, civfr, client, member_id) -> Optional[str]:
    match = db.get_match(message_id)
    if not match or match.validated:
        return "Le match n'existe pas ou a déjà été validé"
    db.valid_match(match)
    # update Players Stats database
    for i in match.report.players:
        db.register_plstats(i.id,
                            match.report.gametype,
                            i.position <= POSITION_REQUIRE_FOR_WIN[match.report.gametype])
    # Verif if players are eligible to new roles
    tasks = [recalc_role_for(civfr.get_member(i.id)) for i in match.report.players]
    await asyncio.gather(*tasks)
    # Change embed
    validation_msg = await client.get_channel(channel_id).fetch_message(match.check_msg_id)
    await validation_msg.edit(embed=match.to_embed(member_id))
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
    async def cmd_getstats(self, *args, member, channel, guild, force, **_):
        if not isinstance(channel, discord.DMChannel) and channel.id != 258920360907374593 and not force:
            raise Forbidden("Arrêtez de spam les mauvais chan")
        if not args:
            target = member
        else:
            name = ' '.join(args)
            target = get_member(guild, name)
            if not target:
                raise NotFound(f"Member named \"{name}\" not found")
        pl = db.get_stat_for(target.id)
        await channel.send(str(pl))

    async def cmd_setcivfr(self, *args, member, guild, channel, force, client, **_):
        if not is_arbitre(member, client=client) and not force:
            raise Forbidden("You must be Arbitre for use this command")
        member = guild.get_member(int(args[0]))
        if not member:
            raise NotFound(f"Member {args[0]} not found")
        db.manual_query_set(*args)
        await channel.send("Stats changed")
        await recalc_role_for(member)

    async def cmd_unvalidreport(self, *args, member, force, client, channel, **_):
        if not is_arbitre(member, client=client) and not force:
            raise Forbidden("You must be Arbitre for use this command")
        if not args:
            raise InvalidArgs("Command must take one argument")
        if not args[0].isdigit():
            raise InvalidArgs("Argument must be a number")
        match = db.get_match(args[0])
        if not match:
            raise NotFound("Match not found")
        if not match.validated:
            raise BotError("Match is already unvalided")
        db.unvalid_match(match)
        # update Players Stats database
        for i in match.report.players:
            db.unregister_plstats(i.id,
                                match.report.gametype,
                                i.position <= POSITION_REQUIRE_FOR_WIN[match.report.gametype])
        # Verif if players are eligible to new roles
        civfr: discord.Guild = client.get_guild(CIVFR_GUILD_ID)
        tasks = [recalc_role_for(civfr.get_member(i.id)) for i in match.report.players]
        await asyncio.gather(*tasks)
        # Change embed
        validation_msg = await client.get_channel(REPORT_CHANNEL).fetch_message(match.check_msg_id)
        await validation_msg.edit(embed=match.to_embed(member.id))
        await validation_msg.clear_reactions()
        await channel.send("Match invalidé.")

    async def cmd_validreport(self, *args, member, force, client, guild, channel, **_):
        if not is_arbitre(member, client=client) and not force:
            raise Forbidden("You must be Arbitre for use this command")
        if not args:
            raise InvalidArgs("Command must take one argument")
        if not args[0].isdigit():
            raise InvalidArgs("Argument must be a number")
        r = await valid_report(int(args[0]), channel.id, guild, client, member)
        if r:
            raise BotError(r)
        else:
            await channel.send("Report validé de force")


    @only_owner
    async def cmd_civfrgivelvl20(self, *args, channel, guild : discord.Guild, **_):
        R = [652143977260122125, 682919453788471306, 682245125656805459, 708475004744106024, 708475862860824598, 751869750660956220,
             708475012624941107, 708475021621723137, 708475860348567612, 708475861606596612, 708475862693052438, 708475864110596107
             ]

        i = 0
        members = guild.members
        for member in members:
            for role in member.roles:
                if role.id in R:
                    db.set(member.id, "great_player", 1)
                    await recalc_role_for(member)
                    await channel.send(f"Le lvl 20 a été donnée à {member.mention} car il fait partie de l'équipe {role.mention}", allowed_mentions=discord.AllowedMentions(users=False, roles=False))
                    break
            i += 1
            if i % 500 == 0:
                await channel.send(f"Progression: {i}/{len(members)}")
        await channel.send("DONE")

    @only_owner
    async def cmd_civfrgivelvl10(self, *args, channel, guild : discord.Guild, **_):
        from datetime import datetime, timedelta
        lvl10cap = datetime.now() - timedelta(days=365//2)
        i = 0
        members = guild.members
        for member in members:
            if member.joined_at < lvl10cap:
                try:
                    db.set(member.id, "longdate_member", 1)
                    await recalc_role_for(member)
                    print(f"Gived lvl 10 to {member}")
                except Exception as e:
                    print(e)
            i += 1
            if i % 500 == 0:
                await channel.send(f"Progression: {i}/{len(members)}")
        await channel.send("DONE")

    @only_owner
    async def cmd_civfrrefreshallroles(self, *args, client, channel, **_):
        players_id : List[id] = db.get_all_players()
        civfr = client.get_guild(CIVFR_GUILD_ID)
        i = 0
        for discord_id in players_id:
            member = civfr.get_member(discord_id)
            if not member:
                continue
            try:
                await recalc_role_for(member)
            except:
                pass
            i += 1
            if i % 50 == 0:
                await channel.send(f"Progression: {i}/{len(players_id)}")

