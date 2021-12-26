import nextcord
import json
import asyncio
from pantheon import pantheon
from util.decorator import only_owner
from util.exception import Error, InvalidArgs, NotFound, ALEDException
from util.function import load_json_file, write_json_file

LEAGUE_SCORE = {"IRON": 0, "BRONZE":500, "SILVER":1000, "GOLD":1500, "PLATINUM":2000,
                "DIAMOND":2500, "MASTER":2600, "GRANDMASTER": 2600, "CHALLENGER":2600}
DIV_SCORE = {"IV":0,"III":110,"II":220,"I":330}
QUEUE = {"RANKED_FLEX_SR":"FlexQ", "RANKED_SOLO_5x5":"SoloQ", "RANKED_FLEX_TT":"3v3TT", "RANKED_TFT":"TFT"}
with open("private/rgapikey") as key:
    panth = pantheon.Pantheon("euw1", key.read(), True)

def load_verif():
    return load_json_file("data/summoners")

def load_score():
    return load_json_file("data/rank_score")

def save_score(dic):
    return write_json_file("data/rank_score", dic)

async def get_leader(message, rank):
    scores = load_score()
    verif = load_verif()
    guild = message.guild
    if not guild:
        raise Error("Impoissble de récupérer le classement du serveur")
    guildv = [str(verif[str(member.id)]) for member in guild.members if str(member.id) in verif.keys()]
    l = [(player, score[rank]) for player, score in scores.items()
            if player in guildv and rank in score.keys()]
    l = sorted(l, key=lambda x: x[1][0])[::-1]
    return l

async def get_leaderboard_place(message, summ_id, rank):
    summ_id = str(summ_id)
    scores = load_score()
    if summ_id not in scores.keys():
        return None
    if rank not in scores[summ_id].keys():
        return None
    verif = load_verif()
    guild = message.guild
    if not guild:
        raise Error("Impoissble de récupérer le classement du serveur")
    guildv = [str(verif[str(member.id)]) for member in guild.members if str(member.id) in verif.keys()]
    l = [(player, score[rank][0]) for player, score in scores.items()
            if player in guildv and rank in score.keys()]
    l = sorted(l, key=lambda x: x[1])[::-1]
    return ([i[0] for i in l].index(summ_id) + 1, len(l))

async def get_ranked_score(summoner_id: str) -> dict:
    data = await panth.getLeaguePosition(summoner_id)
    pos = {QUEUE[i["queueType"]]:
            (LEAGUE_SCORE[i['tier']] + DIV_SCORE[i['rank']] + i['leaguePoints'],
             "{:>8} {rank:<3} {leaguePoints:^3}LP".format(i['tier'].capitalize(), **i))
           for i in data}
    return pos

class CmdLolScore:
    @only_owner
    async def cmd_refreshallscore(self, *args, message, **_):
        msg = await message.channel.send("Calcul des scores")
        verif = load_verif()
        dic = {i:await get_ranked_score(i) for i in verif.values()}
        save_score(dic)
        await msg.edit(content="{} scores ont été mis à jour".format(len(dic)))

    async def cmd_ladder(self, *args, message, **_):
        if not args or args[0] not in ['SoloQ', 'FlexQ', '3v3TT', 'TFT']:
            raise InvalidArgs("Préciser la queue [SoloQ/FlexQ/3v3TT/TFT]")
        lst = await get_leader(message, args[0])
        lst = lst[:20]
        tasks = [panth.getSummoner(summ_id) for summ_id in [i[0] for i in lst]]
        summ_name = [i['name'] for i in await asyncio.gather(*tasks)]
        txt = "```{}```".format('\n'.join(["{:>2}.{:>16} {}".format(i+1, summ_name[i], j[1][1])
                                for i,j in enumerate(lst)]))
        await message.channel.send(txt)

    async def cmd_info(self, *args, message, member, **_):
        summ_id, name = None, None
        if not args:
            verif = load_verif()
            if str(member.id) in verif:
                summ_id = verif[str(member.id)]
            else:
                name = member.display_name
        else:
            name = " ".join(args)
        if summ_id:
            data = await panth.getSummoner(summ_id)
        else:
            data = await panth.getSummonerByName(name)
        if not data:
            raise NotFound("Impossible de trouver l'invocateur")
        icon = "http://ddragon.canisback.com/latest/img/profileicon/"+str(data['profileIconId'])+".png"
        score = load_score()
        score[data['id']] = await get_ranked_score(data['id'])
        txt = ""
        for i in ["SoloQ", "FlexQ", "3v3TT", "TFT"]:
            lead = await get_leaderboard_place(message, data['id'], i)
            if lead:
                txt += "``{}: {} {:>2}/{}``\n".format(i, score[str(data['id'])][i][1], *lead)
        colour = 0xDDDDDD
        if summ_id:
            colour = member.colour
        elif message.guild:
            target = message.guild.get_member_named(name)
            if target : colour = target.colour
        em = nextcord.Embed(title="Information de l'invocateur", description=txt + "", colour=colour)
        em.set_author(name=data['name'], icon_url=icon)
        await message.channel.send(embed=em)
        save_score(score)
