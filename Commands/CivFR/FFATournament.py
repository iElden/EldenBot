from typing import List, Dict, Generator, Set
import re
import discord
import asyncio
from datetime import datetime, timedelta
import json

from util.exception import InvalidArgs, Forbidden
from .utils import is_arbitre
from .exc import ParsingError
from .constant import DIDON, ARBITRE_ID, CIVFR_GUILD_ID

MENTION = re.compile(".*<@!?(\d+)>.*")
POINTS = [18, 15, 12, 9, 6, 5, 4, 2] + [0] * 5
STARS = [3, 2, 1] + [0] * 10
POS_STR = ["1er", "2eme", "3eme", "4eme", "5eme", "6eme", "7eme", "8eme", "9eme", "10eme", "11eme", "12eme", "Quit"]
WEEKS = [datetime(2020, 5, 26), datetime(2020, 6, 1), datetime(2020, 6, 8), datetime(2020, 6, 15)]
#REPORT_CHANNEL = 714564031737757876
REPORT_CHANNEL = 714893257301032992
LEADERBOARD_CHANNEL_ID = 714987001954304010
LEADERBOARD_MESSAGE_ID = 714995778116124791

class Database:

    FILE = "data/ffatournament.json"

    def __init__(self):
        with open(self.FILE) as fd:
            self.matchs = [Match.from_json(i) for i in json.load(fd)]  # type: List[Match]

    def add_match(self, match):
        self.matchs.append(match)
        self.save()

    def get_history_for(self, player_id : int) -> Generator:
        return (match for match in self.matchs if player_id in match.result_dict.keys() and match.is_valided)

    def get_match(self, match_id : int):
        for match in self.matchs:
            if match_id == match.report_message_id or match_id == match.confirm_message_id:
                return match
        return None

    def get_all_players(self) -> Set[int]:
        players = set()  # type: Set[int]
        for match in self.matchs:
            for player in match.result_dict.keys():
                players.add(player)
        return players

    def save(self):
        with open(self.FILE, 'w') as fd:
            json.dump([i.to_json() for i in self.matchs], fd)

class Match:
    def __init__(self, result_dict, report_message_id, confirm_message_id, is_valided, date):
        self.result_dict = result_dict
        self.report_message_id = report_message_id
        self.confirm_message_id = confirm_message_id
        self.is_valided = is_valided
        self.date = date  # type: datetime
        self.date_str = date.strftime("%d/%m")

    def to_json(self) -> dict:
        return {
            "result_dict": {str(k): v for k, v in self.result_dict.items()},
            "report_message_id": self.report_message_id,
            "confirm_message_id": self.confirm_message_id,
            "is_valided": self.is_valided,
            "date": self.date.strftime("%d/%m/%Y %H:%M:%S")
        }

    @classmethod
    def from_json(cls, js):
        return cls({int(k): v for k, v in js['result_dict'].items()}, js['report_message_id'], js['confirm_message_id'],
                   js['is_valided'], datetime.strptime(js['date'], "%d/%m/%Y %H:%M:%S"))

    @staticmethod
    def parse_report(txt) -> Dict[int, int]:
        result = {}  # type: Dict[int, int]
        pos = 0
        for line in txt.split('\n'):
            r = MENTION.findall(line)
            if r:
                for i in r:
                    result[int(i)] = pos
                pos += len(r)
        return result

    def __getitem__(self, item):
        return self.result_dict[item]

class PlMatch:
    def __init__(self, match, is_best, player_id):
        self.match = match
        self.is_best = is_best
        self.player_id = player_id

    def __str__(self):
        pos = self.match[self.player_id]
        base = f"{'+' if self.is_best else '-'} {self.match.date_str}: {POS_STR[pos]}"
        if self.is_best:
            return base + f" (+{POINTS[pos]} pts / +{STARS[pos]} ⭐)"
        return base

    @property
    def points(self):
        return POINTS[self.match[self.player_id]]

    @property
    def stars(self):
        return STARS[self.match[self.player_id]]

    def __getitem__(self, item):
        return self.match[item]

async def update_leaderboard(client):
    channel = client.get_channel(LEADERBOARD_CHANNEL_ID)
    msg = await channel.fetch_message(LEADERBOARD_MESSAGE_ID)

    result = {}  # type: Dict[int, Tuple[int, int]]
    players = db.get_all_players()
    for player in players:
        history = keep_best_matches(db.get_history_for(player), player)
        points = sum(plMatch.points for plMatch in history if plMatch.is_best)
        stars = sum(plMatch.stars for plMatch in history if plMatch.is_best)
        result[player] = (points, stars)

    sorted_result = sorted(result.items(), key=lambda i: i[1], reverse=True)
    # txt = '\n'.join(f"{i+1} : <@{result[0]}> {result[1][0]} pts / {result[1][1]} ⭐" for i, result in enumerate(sorted_result[:15]))
    em = discord.Embed(title="Classement tournoi FFA")
    em.add_field(name="Joueurs",
                 value= '\n'.join(f"{i+1} : <@{result[0]}>" for i, result in enumerate(sorted_result[:25]))
    )
    em.add_field(name="Points",
                 value= '\n'.join(f"{result[1][0]} pts / {result[1][1]} ⭐" for i, result in enumerate(sorted_result[:25]))
    )
    await msg.edit(embed=em)

async def on_report(message):
    if message.channel.id != REPORT_CHANNEL:
        return
    result = Match.parse_report(message.content)
    result_len = len(result)
    if result_len <= 1:
        return
    if result_len < 6:
        raise ParsingError(f"Le rapport de match doit contenir au moins 6 mentions. {result_len} mentions ont été parsé.")
    date = message.created_at - timedelta(hours=6)
    em = discord.Embed(title="Match enregistré", description='\n'.join(f"{v+1} : <@{k}>" for k, v in result.items()))
    em.add_field(name="Status : En attente de validation", value="Un arbitre doit dindoner pour que votre partie soit comptée dans le score.")
    em.set_footer(text=f"Report by: {message.author}")
    msg = await message.channel.send(embed=em)  # type: discord.Message
    db.add_match(Match(result, message.id, msg.id, False, date))
    await msg.add_reaction(DIDON)

async def on_dindon(payload : discord.RawReactionActionEvent, *, client : discord.Client):
    if payload.channel_id != REPORT_CHANNEL and payload.emoji != DIDON:
        return
    channel = client.get_channel(payload.channel_id)
    civ_fr = client.get_guild(CIVFR_GUILD_ID)  # type: discord.Guild
    member = civ_fr.get_member(payload.user_id)
    if not member or (not is_arbitre(member) and payload.user_id != 384274248799223818):
        return
    match = db.get_match(payload.message_id)
    if match.is_valided:
        return
    msg = await channel.fetch_message(payload.message_id)
    em = discord.Embed(title="Match validé", description='\n'.join(f"{v+1} : <@{k}>" for k, v in match.result_dict.items()))
    em.add_field(name="Status : Validé !", value=f"Votre match a été validé par {member.mention}.")
    await msg.edit(embed=em)
    match.is_valided = True
    db.save()
    await update_leaderboard(client)

async def on_init(client):
    await update_leaderboard(client)

def keep_best_matches(history : Generator, player_id) -> List[PlMatch]:
    result = []  # type: List[PlMatch]
    date = None
    best_game_id = None

    # Get best game of each day
    for i, match in enumerate(history):  # type: int, Match
        is_best = False
        if match.date.date() != date:
            date = match.date.date()
            best_game_id = i
            is_best = True
        else:
            best_day_game = result[best_game_id]
            if best_day_game[player_id] > match[player_id]:
                best_day_game.is_best = False
                is_best = True
        result.append(PlMatch(match, is_best, player_id))

    # Get 4 best game of each week
    weeks_matchs = []  # type: List[List[PlMatch]]
    for week in WEEKS[1:]:
        weeks_matchs.append([plMatch for plMatch in result if plMatch.match.date < week and plMatch.is_best])
    for wm in weeks_matchs:
        if len(wm) <= 4:
            continue
        sort = sorted(wm, key=lambda plMatch: plMatch.match.result_dict[player_id], reverse=True)
        for plMatch in sort[4:]:
            plMatch.is_best = False

    return result

async def add_match(*args, client, member, force, channel, **_):
    if len(args) < 1:
        raise InvalidArgs("Match ID is needed")
    if not args[0].isdigit():
        raise InvalidArgs("Match ID must be a int")
    if not is_arbitre(member) and not force:
        raise Forbidden("Only a Arbitre can use this command")
    report_channel = client.get_channel(714564031737757876)  # type: discord.TextChannel
    msg = await report_channel.fetch_message(int(args[0]))
    date = msg.created_at - timedelta(hours=6)
    result = Match.parse_report(msg.content)
    result_len = len(result)
    if result_len <= 1:
        return
    if result_len < 6:
        raise ParsingError(f"Le rapport de match doit contenir au moins 6 mentions. {result_len} mentions ont été parsé.")
    db.add_match(Match(result, msg.id, None, True, date))
    await channel.send(f"Le match {msg.id} a bien été ajouté et vérifié")
    await update_leaderboard(client)


async def force_valid_match(*args : str, member, force, channel, client, **_):
    if len(args) < 1:
        raise InvalidArgs("Match ID is needed")
    if not args[0].isdigit():
        raise InvalidArgs("Match ID must be a int")
    if not is_arbitre(member) and not force:
        raise Forbidden("Only a Arbitre can use this command")
    match = db.get_match(int(args[0]))
    match.is_valided = True
    db.save()
    await channel.send(f"Le match {match.report_message_id}/{match.confirm_message_id} opposant {', '.join(f'<@{i}>' for i in match.result_dict.keys())} a été validé de force par {member.mention}")
    await update_leaderboard(client)

async def show_history(*args : str, member, channel, message, **_):
    if args:
        l = message.mentions
        if len(l) != 1:
            raise InvalidArgs("Mentionnez une et une seule personne dont vous souhaitez voir l'historique (Il y a trop de monde sur ce serveur, j'ai eu la flemme de faire un gros truc)")
        target = l[0]
    else:
        target = member
    history = db.get_history_for(target.id)
    history = keep_best_matches(history, target.id)
    await channel.send("```diff\n{}```".format('\n'.join(str(match) for match in history)))

db = Database()
commands = {
    "valid": force_valid_match,
    "history": show_history,
    "addmatch": add_match
}

class CmdFFATournament:
    async def cmd_ffa(self, *args, **kwargs):
        if not args:
            raise InvalidArgs(f"Aucune sous-commande donnée. Veuillez entrez une des sous-commandes valides suivante: {'/'.join(commands.keys())}")
        cmd = commands.get(args[0])
        if not cmd:
            raise InvalidArgs(f"Sous-commande donné inconnue. Veuillez entrez une des sous-commandes valides suivante: {'/'.join(commands.keys())}")
        await cmd(*args[1:], **kwargs)

