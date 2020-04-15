from util.exception import CommandCanceled, ALEDException

from typing import Dict, Tuple
import discord
import random
import asyncio

class LinqGame:

    def __init__(self, players, mj, channel, client):
        if len(players) < 2:
            raise CommandCanceled("You need at least 4 players for start the game")
        self.mj = mj
        self.players = players
        self.scoreboard = Scoreboard(players)
        self.max_round = 20
        self.round = 1
        self.wordlist = None  # Loaded in load_wordlist
        self.channel = channel
        self.discord_client = client

    async def run(self):
        await self.load_wordlist()
        while self.round <= self.max_round:
            await self.do_round()
            self.round += 1

    async def do_round(self):
        linqround = LinqRound(self)
        result = await linqround.run()
        await self.send_result(result)


    async def send_result(self, result):
        em = result.to_embed()
        txt = self.scoreboard.update_and_return_codeblock(result)
        em.add_field(name="Final Scoreboard", value=txt, inline=False)
        await self.channel.send(embed=em)

    async def run_configurer(self):
        ...

    async def load_wordlist(self):
        msg = await self.channel.send("Loading wordlist...")
        try:
            with open("tmp_wordlist_linq") as fd:
                self.wordlist = [i for i in (line.strip() for line in fd.read().split('\n')) if i]
        except FileNotFoundError:
            raise ALEDException("Cannot find \"./tmp_wordlist_linq\" in directory")
        random.shuffle(self.wordlist)
        await msg.edit(content=f"{len(self.wordlist)} words loaded")


class LinqRound:

    def __init__(self, game):
        self.game : LinqGame = game
        self.counter_spy = self.game.players[:]
        self.spy = []
        for i in range(2):
            spy = random.choice(self.counter_spy)
            self.counter_spy.remove(spy)
            self.spy.append(spy)
        self.passwd = self.game.wordlist.pop()


    async def run(self): # -> RoundResult
        await self.announce_role()
        await self.game.channel.send(f"{self.game.mj.mention}: Merci d'envoyer ``OK`` quand le round est terminé (Round {self.game.round}/{self.game.max_round})")
        await self.game.discord_client.wait_for('message', check=lambda m: m.author == self.game.mj and m.content == "OK")
        tasks = [self.ask_accusation(i) for i in self.game.players]
        accusation_result = await asyncio.gather(*tasks)
        return RoundResult(self, self.game.players, accusation_result)

    async def ask_accusation(self, player):
        print(f"started accusation for {player}")
        if player in self.spy:
            em = discord.Embed(
                title="Trouvez votre allié",
                description=self.get_player_list(exclude=player)).set_footer(text="Entre le nom de la personne dans le canal")
            asyncio.ensure_future(player.send(embed=em))
            while True:
                msg = await self.game.discord_client.wait_for('message', check=lambda m: m.author == player and m.channel == player.dm_channel)
                pl = self.find_player(msg.content)
                if pl == player:
                    asyncio.ensure_future(player.send("Vous ne pouvez pas vous désigner vous-même", delete_after=10))
                    continue
                if pl:
                    break
                asyncio.ensure_future(player.send("Joueur non trouvé", delete_after=10))
            print("OK S")
            return [pl]

        # if player is a counter-spy
        bot_msg = await player.send(embed=discord.Embed(title="Loading ..."))
        player_list = self.get_player_list(exclude=player)
        r1 = r2 = None
        while True:
            em = discord.Embed(title="Rapport de contre espionnage",
                               ).set_footer(text="Entre le nom de la personne dans le canal")
            em.add_field(name="Liste des joueurs", value=player_list)
            em.add_field(name="Liste des joueurs",
                         value=f"Espion 1: {r1.mention if r1 else '...'}\nEspion 2:{r2.mention if r2 else '...'}",
                         inline=False)
            asyncio.ensure_future(bot_msg.edit(embed=em))
            if r1 and r2:
                print("OK CS")
                return [r1, r2]
            msg = await self.game.discord_client.wait_for('message', check=lambda
                m: m.author == player and m.channel == player.dm_channel)
            pl = self.find_player(msg.content)
            if pl == player:
                asyncio.ensure_future(player.send("Vous ne pouvez pas vous désigner vous-même", delete_after=10))
                continue
            if pl and not r1:
                r1 = pl
            elif pl and r1:
                r2 = pl
            else:
                asyncio.ensure_future(player.send("Joueur non trouvé", delete_after=10))



    async def announce_role(self):
        spy_em = discord.Embed(title="Vous êtes un espion !", description=f"Le code secret que vous devez faire passer est ``{self.passwd}``")
        for spy in self.spy:
            asyncio.ensure_future(spy.send(embed=spy_em))
        counter_spy_em = discord.Embed(title="Vous êtes un contre-espion !", description="Démasquez les espions")
        for counter_spy in self.counter_spy:
            asyncio.ensure_future(counter_spy.send(embed=counter_spy_em))

    def get_player_list(self, exclude=None):
        return "```\n{}```".format('\n'.join(f"- {pl.name}" for pl in self.game.players if pl != exclude))

    def find_player(self, query):
        for pl in self.game.players:
            if query.lower() == pl.name.lower():
                return pl
        return None


class Scoreboard:
    def __init__(self, players, init_score=0):
        self._scoreboard = {i: init_score for i in players}

    def __getitem__(self, item):
        return self._scoreboard.get(item, None)

    def __setitem__(self, key, value):
        self._scoreboard[key] = value

    def __iter__(self):
        for player, score in sorted(self._scoreboard.items(), key=lambda x: x[1], reverse=True):
            yield (player, score)

    def get_scoreboard_embed(self):
        txt = ""
        ls = sorted(self._scoreboard.items(), key=lambda x: x[1], reverse=True)
        for i, (player, score) in enumerate(ls):
            txt += f"{i}. {player.mention}: {score}\n"
        em = discord.Embed(title="Tableau des scores", description=txt, colour=ls[0].colour)
        return em

    def update(self, roundresult):
        d = {player:sum(dic.values()) for player, dic in roundresult.player_report.items()}
        for player, dic in roundresult.player_report.items():
            self[player] += sum(dic.values())
        return d

    def update_and_return_codeblock(self, roundresult):
        d = self.update(roundresult)
        max_player_name = max(len(i.name) for i in self._scoreboard.keys())
        txt = "```diff\n"
        for player, score in self:
            txt += f"{'+' if score >= 0 else '-'} {player.name:>{max_player_name}}: {score:<3}({d[player]:+})\n"
        return txt + "```"


class RoundResult:
    def __init__(self, linqround, players, acc_result):
        self.player_report = {} # type: Dict[discord.Member, Dict[str, int]]

        accusations = {i:j for i,j in zip(players, acc_result)}

        for pl, acc in accusations.items():
            self.player_report[pl] = {}
            if len(acc) == 1:  # spy
                if acc[0] in linqround.spy:
                    self.player_report[pl]["Allié trouvé"] = 1
                    if accusations[acc[0]][0] == pl:
                        self.player_report[pl]["Allié trouvé réciproquement"] = 2
            elif len(acc) == 2: #counter-spy
                if acc[0] in linqround.spy and acc[1] in linqround.spy:
                    self.player_report[pl][f"{acc[0].name} démasqué"] = 1
                    self.player_report[pl][f"{acc[1].name} démasqué"] = 1
                    self.player_report[acc[0]][f"repéré par {pl.name}"] = -1
                    self.player_report[acc[1]][f"repéré par {pl.name}"] = -1
            else:
                raise ALEDException(f"{pl} returned a accusation list of length {len(acc)}, excepted 1 or 2")

    def to_embed(self):
        em = discord.Embed(title="Détail des scores")
        for pl, dic in self.player_report.items():
            em.add_field(name=pl.name, value=self.dic_to_codeblock(dic))
        return em

    @staticmethod
    def dic_to_codeblock(dic):
        txt = "```diff\n"
        for reason, point in dic.items():
            txt += f"{'+' if point >= 0 else '-'} {reason} ({point:+})\n"
        return txt + '```'



class CmdLinq:
    async def cmd_linq(self, *__, message, member, channel, client, **_):
        linq = LinqGame(message.mentions, member, channel, client)
        await linq.run()
