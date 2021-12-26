from pantheon import pantheon
from util.decorator import not_offical_serv, only_owner
from util.exception import InvalidArgs, NotFound
from constant import CHAMP_ID_TO_EMOJI, RUNE_ID_TO_EMOJI, MASTERIES_TO_EMOJI, CHAMP_NONE_EMOJI, INVISIBLE_EMOJI
from .lol_score import LEAGUE_SCORE, DIV_SCORE
import asyncio
import nextcord
import time

from .verif import load_verif

SEASON = 13
SHORT_LEAGUE = {
    "IRON": "Iron",
    "BRONZE": "Bronze",
    "SILVER": "Silver",
    "GOLD": "Gold",
    "PLATINUM": "Plat",
    "DIAMOND": "Diam",
    "MASTER": "Master",
    "GRANDMASTER": "G Mast",
    "CHALLENGER": "Chall"
}
SHORT_DIV = {
    "V": 5,
    "IV": 4,
    "III": 3,
    "II": 2,
    "I": 1
}

with open("private/rgapikey") as key:
    panth = pantheon.Pantheon("euw1", key.read(), True)

def get_player_id(pi, accid):
    for i in pi:
        if i["player"]["accountId"] == accid:
            return i["participantId"]
    return None

async def get_bonus(summonerId, win, totalMatches):
    bonus = {}
    winrate = round((win / totalMatches) * 100)
    mastery = await panth.getChampionMasteries(summonerId)
    mastery7 = [i["championId"] for i in mastery if i["championLevel"] == 7]
    if winrate >= 60 : bonus["High Winrate ({}%)".format(str(winrate))] = 1
    if winrate <= 40 : bonus["Low Winrate ({}%)".format(str(winrate))] = -1
    if 157 in mastery7 : bonus["Yasuo masteries 7"]  = 1
    if 40  in mastery7 : bonus["Janna masteries 7"]  = -0.5
    if 16  in mastery7 : bonus["Soraka masteries 7"] = -0.5
    if 267 in mastery7 : bonus["Nami masteries 7"] = -0.5
    if 117 in mastery7 : bonus["Lulu masteries 7"] = -0.5
    return (bonus)



async def getLeagueSoloQ(summonerId):
    data = await panth.getLeaguePosition(summonerId)
    for league in data:
        if league['queueType'] == 'RANKED_SOLO_5x5':
            return (league)
    return (None)

async def getSummoner(name):
    try:
        data = await panth.getSummonerByName(name)
        return (data["accountId"], data["id"], data["profileIconId"])
    except:
        return (None, None, None)

async def getLastYearHistory(accountId):
    index = 0
    tasks = []
    begin = int(time.time()) * 1000 - 31536000000
    while True:
        matchs = await panth.getMatchlist(accountId, params={"beginIndex":index, "beginTime":begin})
        tasks += [panth.getMatch(match["gameId"]) for match in matchs['matches']]
        index += 100
        if matchs["endIndex"] != index: break
    return await asyncio.gather(*tasks)

async def getSoloQSeasonMatches(accountId):
    soloQ =  await panth.getMatchlist(accountId, params={"queue":420,"season":SEASON})
    matchlist = soloQ['matches']
    #flexQ = await panth.getMatchlist(accountId, params={"queue":440,"season":11})
    #matchlist += flexQ['matches']
    tasks =  [panth.getMatch(match["gameId"]) for match in matchlist]
    return await asyncio.gather(*tasks)

async def getSeasonMatches(accountId, timeline=False):
    matches =  await panth.getMatchlist(accountId, params={"season":SEASON})
    matchlist = matches['matches']
    tasks = [panth.getMatch(match["gameId"]) for match in matchlist]
    if timeline:
        timelines = [panth.getTimeline(match["gameId"]) for match in matchlist]
        allMatches  = await asyncio.gather(*tasks)
        allTimeline = await asyncio.gather(*timelines)
        return (allMatches, allTimeline)
    return await asyncio.gather(*tasks)

class CmdRgapi:
    async def cmd_premade(self, *args, message, member, **_):
        if not args : summonerName = member.name
        else : summonerName = " ".join(args)
        accountId, summonerId, iconId = await getSummoner(summonerName)
        if not accountId:
            raise InvalidArgs("Invocateur non trouvé")
        result = {}
        msg = await message.channel.send("Récupération de l'historique")
        matchs = await getLastYearHistory(accountId)
        await msg.edit(content="Analyse des matchs")
        for match in matchs:
            for player in [i["player"]["summonerId"] for i in match["participantIdentities"]
                           if "summonerId" in i["player"].keys()
                           and i["player"]["summonerId"] != summonerId]:
                if player in result.keys(): result[player] += 1
                else : result[player] = 1
        await msg.edit(content="Tri des données")
        result = {player : nb for player, nb in result.items() if nb >= 5}
        r = sorted(result.items(), key=lambda x: x[1])[::-1]
        await msg.edit(content="Récupération des noms d'invocateur")
        tasks = [panth.getSummoner(summonerId) for summonerId, nb in r]
        response = await asyncio.gather(*tasks)
        txt = "```{}```".format(
            "\n".join(["{:>3}: {}".format(r[i][1], response[i]['name']) for i in range(len(r))]))
        if len(txt) >= 2000 : txt = txt[:1996] + "```"
        em = nextcord.Embed(title="Invocateurs rencontrés les 365 derniers jours",
                           description=txt)
        em.set_author(name=summonerName,
                      icon_url="http://ddragon.canisback.com/latest/img/profileicon/"+str(iconId)+".png")
        await msg.edit(content="done", embed=em)

    @only_owner
    async def cmd_getsummid(self, *args, message, **_):
        d = await panth.getSummonerByName(' '.join(args))
        await message.channel.send("ID : {id}\naccountId : {accountId}\npuuid : {puuid}".format(
            **d
        ))


    @not_offical_serv
    async def cmd_kikimeter(self, *args, message, member, **_):
        """/kikimeter {*nom d'invocateur}"""
        if not args: summonerName = member.name
        else : summonerName = "".join(args)
        accountId, summonerId, iconId = await getSummoner(summonerName)
        if not accountId or not summonerId:
            raise NotFound("Invocateur : {} non trouvé".format(summonerName))
        league = await getLeagueSoloQ(summonerId)
        if not league:
            return await message.channel.send("Cet invocateur n'est pas classé en SoloQ (et il y a que ça qui compte)")
        msg = await message.channel.send("Récupération des données en cours ...")
        dic1 = {"BRONZE":1,"SILVER":1.5,"GOLD":2.2,"PLATINUM":3,"DIAMOND":4,"MASTER":4.5,"CHALLENGER":5.5}
        dic2 = {"V":0.0, "IV":0.1, "III":0.3, "II":0.4, "I":0.5}
        league_bonus = dic1[league['tier']] + dic2[league['rank']]
        seasonMatches = await getSoloQSeasonMatches(accountId)
        kills, deaths, assists, damage, duration, win = 0, 0, 0, 0, 0, 0
        for match in seasonMatches:
            id = get_player_id(match["participantIdentities"], accountId)
            stat = match["participants"][id - 1]["stats"]
            kills += stat["kills"]
            deaths += stat["deaths"]
            assists += stat["assists"]
            damage += stat["totalDamageDealt"]
            duration += match["gameDuration"]
            win += stat["win"]
        bonus = await get_bonus(summonerId, win, len(seasonMatches))
        total_bonus = sum(bonus.values())
        if not deaths: deaths = 0.75
        kda = round((kills + assists * 0.75) / deaths, 2)
        dps = round(damage / duration, 2)
        epenis = round(((kills + assists * 0.75) / deaths + damage / duration / 40) * league_bonus + total_bonus * (league_bonus / 2), 2)
        average_kda = [str(round(i / len(seasonMatches), 1)) for i in [kills, deaths, assists]]
        title = "{} possède un e-penis de {} cm\n".format(summonerName, epenis)
        recap =  "__Recap des points__:\n"
        recap += "KDA ({}) : **{}**\n".format("/".join(average_kda), str(kda))
        recap += "DPS ({}) : **{}**\n".format(dps, round(damage / duration / 40, 2))
        recap += "Multiplicateur ({} {}) : **x{}**\n".format(league['tier'].capitalize(), league['rank'], league_bonus)
        if bonus : recap += "BONUS / MALUS : ```diff"
        for i, j in bonus.items():
            recap += "\n{} {} : {}".format("-" if j < 0 else "+", i, str(j))
        if bonus : recap += "```"
        try : colour = message.guild.get_member_named(summonerName).colour
        except : colour = 0xC0C0C0
        em = nextcord.Embed(title=title, description=recap, colour = colour)
        em.set_footer(text="INFO : " + str(len(seasonMatches)) + " matchs analysés")
        em.set_author(name=summonerName, icon_url="http://ddragon.canisback.com/latest/img/profileicon/"+str(iconId)+".png")
        await msg.edit(content=".",embed=em)

    @not_offical_serv
    async def cmd_afkmeter(self, *args, message, member, **_):
        """/afkmeter {*nom d'invocateur}"""
        count = {}
        if not args: summonerName = member.name
        else : summonerName = "".join(args)
        accountId, summonerId, iconId = await getSummoner(summonerName)
        if not accountId :
            raise NotFound("Invocateur non trouvé : {}".format(summonerName))
        try : colour = message.guild.get_member_named(summonerName).colour
        except : colour = 0xC0C0C0
        icon = "http://ddragon.canisback.com/latest/img/profileicon/"+str(iconId)+".png"
        msg = await message.channel.send(embed=nextcord.Embed(title="Afk Meter",colour=colour).set_author(name=summonerName, icon_url=icon))
        matches, timelines = await getSeasonMatches(accountId, timeline=True)
        for i in range(len(matches)):
            for participant in matches[i]["participantIdentities"]:
                if str(participant["player"]["accountId"]) == str(accountId) :
                    id = str(participant["participantId"])
            oldpos,afk = "None",0
            for frame in timelines[i]["frames"]:
                try : j = frame["participantFrames"][str(id)]["position"]
                except : j = {"x":"None","y":"None"}
                pos = str(j["x"])+","+str(j["y"])
                if pos == oldpos :
                    afk += 1
                    if afk >= 2:
                        try: count[str(matches[i]["gameId"])] += 1
                        except: count[str(matches[i]["gameId"])] = 2
                else: afk = 0
                oldpos = pos
        txt, nb, mt = "", 0, 0
        for x,y in count.items():
            txt += "\ngame n°" + str(x) +" : **" + str(y) +"** minute(s)"
            nb += 1
            mt += y
        em = nextcord.Embed(title="Afk Meter :",description="Sur les " +str(len(matches)) +" dernières parties\n" +summonerName +" a AFK **" +str(nb) +"** games pour un total de **" +str(mt) +"** minutes\n\n" +txt,colour=colour)
        await msg.edit(embed=em.set_author(name=summonerName, icon_url=icon))


    async def cmd_gameinfo(self, *args, member, channel, **_):
        summ_id, name = None, None  # type: str
        if not args:
            verif = load_verif()
            if str(member.id) in verif:
                summ_id = verif[str(member.id)]
            else:
                name = member.display_name
        else:
            name = " ".join(args)
        try:
            if summ_id:
                summ_info = await panth.getSummoner(summ_id)
            else:
                summ_info = await panth.getSummonerByName(name)
        except:
            raise NotFound("Impossible de trouver l'invocateur")
        try:
            spec_data = await panth.getCurrentGame(summ_info["id"])
        except :
            return await channel.send("L'invocateur n'est pas en jeu actuellement")
        msg = await channel.send(embed=nextcord.Embed(title="Récupération des informations ..."))
        team1 = await asyncio.gather(*(format_player_info(participant) for participant in spec_data["participants"] if participant["teamId"] == 100))
        team2 = await asyncio.gather(*(format_player_info(participant) for participant in spec_data["participants"] if participant["teamId"] == 200))

        em = nextcord.Embed(title=f"Game de {summ_info['name']}")
        em.add_field(name="Équipe bleu", value=f"Champions bannis :\n{' '.join([(CHAMP_ID_TO_EMOJI[str(i['championId'])] if str(i['championId']) != '-1' else CHAMP_NONE_EMOJI) for i in spec_data['bannedChampions'] if i['teamId'] == 100])}", inline=False)
        for i, name in enumerate(["Invocateurs", "Runes et Classement", "Masteries"]):
            em.add_field(name=name, value='\n'.join([player[i] for player in team1]), inline=True)

        em.add_field(name="Équipe rouge", value=f"Champions bannis :\n{' '.join([(CHAMP_ID_TO_EMOJI[str(i['championId'])] if str(i['championId']) != '-1' else CHAMP_NONE_EMOJI) for i in spec_data['bannedChampions'] if i['teamId'] == 200])}", inline=False)
        for i, name in enumerate(["Invocateurs", "Runes", "Masteries"]):
            em.add_field(name=name, value='\n'.join([player[i] for player in team2]), inline=True)

        await msg.edit(embed=em)

    async def cmd_tftear(self, *args, channel, **_):
        players = ' '.join(args).split(',')
        summs = await asyncio.gather(*(panth.getSummonerByName(player) for player in players))
        leagues = await asyncio.gather(*(panth.getLeaguePosition(summ['id']) for summ in summs))
        leagues = [[league for league in player_leagues if league['queueType'] == "RANKED_TFT"] for player_leagues in leagues]

        txt = "```"
        for i in range(len(summs)):
            if not leagues[i]:
                txt += "{:>16}: None\n"
            else:
                txt += "{:>16}: {} {} {}LP\n".format(summs[i]['name'],
                                                   SHORT_LEAGUE[leagues[i][0]['tier']],
                                                   SHORT_DIV[leagues[i][0]['rank']],
                                                   leagues[i][0]['leaguePoints'])
        txt += "```"
        await channel.send(txt)


async def format_player_info(data: dict):
    try:
        pos = await panth.getLeaguePosition(data['summonerId'])
        d = [(f"{i['tier'].title()} {i['rank']}", LEAGUE_SCORE[i['tier']] + DIV_SCORE[i['rank']]) for i in pos]
        league_str, _ = max(d, key=lambda x: x[1])
    except:
        league_str = "Unranked"

    player = "{} ``{}``\n{} {}\n".format(CHAMP_ID_TO_EMOJI[str(data["championId"])], data['summonerName'], INVISIBLE_EMOJI, league_str)


    runes = "{}|{}\n{}\n".format(RUNE_ID_TO_EMOJI[str(data['perks']['perkIds'][0])],
                               ''.join([RUNE_ID_TO_EMOJI[str(i)] for i in data['perks']['perkIds'][1:4]]),
                               ''.join([RUNE_ID_TO_EMOJI[str(i)] for i in data['perks']['perkIds'][4:6]]))

    try:
        champ_masteries = await panth.getChampionMasteriesByChampionId(data['summonerId'], data['championId'])
    except:
        champ_masteries = {'championLevel': 0, 'championPoints': 0}
    a = lambda nb: [nb[::-1][i*3:(i+1)*3][::-1] for i in range((len(nb)+2)//3)][::-1]
    score = "{} Level {}\n{} {} points\n".format(MASTERIES_TO_EMOJI.get(str(champ_masteries['championLevel']), INVISIBLE_EMOJI), champ_masteries['championLevel'], INVISIBLE_EMOJI, ' '.join(a(str(champ_masteries['championPoints']))))
    return (player, runes, score)