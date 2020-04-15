from util.exception import CommandCanceled
import discord
import random
import asyncio

class LinqGame:

    def __init__(self, players, mj, channel, client):
        if len(players) < 4:
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
        await linqround.run()


    async def run_configurer(self):
        ...

    async def load_wordlist(self):
        msg = await self.channel.send("Loading wordlist...")
        with open("tmp_wordlist_linq") as fd:
            self.wordlist = [i for i in (line.strip() for line in fd.read().split('\n')) if i]
        random.shuffle(self.wordlist)
        await msg.edit(content=f"{len(self.wordlist)} words loaded")


class LinqRound:

    def __init__(self, game):
        self.game : LinqGame = game
        self.counter_spy = self.game.players[:]
        self.spy = random.choices(self.counter_spy, k=2)
        for spy in self.spy:
            self.counter_spy.remove(spy)
        self.passwd = self.game.wordlist.pop()


    async def run(self):
        await self.announce_role()
        await self.game.channel.send(f"{self.game.mj.mention}: Merci d'envoyer ``OK`` quand le round est terminé (Round {self.game.round}/{self.game.max_round})")
        await self.game.discord_client.wait_for('message', check=lambda m: m.author == self.game.mj and m.content == "OK")


    async def announce_role(self):
        spy_em = discord.Embed(title="Vous êtes un espion !", description=f"Le code secret que vous devez faire passer est ``{self.passwd}``")
        for spy in self.spy:
            asyncio.ensure_future(spy.send(embed=spy_em))
        counter_spy_em = discord.Embed(title="Vous êtes un contre-espion !", description="Démasquez les espions")
        for counter_spy in self.counter_spy:
            asyncio.ensure_future(counter_spy.send(embed=counter_spy_em))




class Scoreboard:
    def __init__(self, players, init_score=0):
        self._scoreboard = {i: init_score for i in players}

    def __getitem__(self, item):
        return self._scoreboard.get(item, None)

    def __setitem__(self, key, value):
        self._scoreboard[key] = value

    def get_scoreboard_embed(self):
        txt = ""
        ls = sorted(self._scoreboard.items(), key=lambda x: x[1], reverse=True)
        for i, (player, score) in enumerate(ls):
            txt += f"{i}. {player.mention}: {score}"
        em = discord.Embed(title="Tableau des scores", description=txt, colour=ls[0].colour)
        return em

class CmdLinq:
    async def cmd_linq(self, *__, message, member, channel, client, **_):
        linq = LinqGame(message.mentions * 4, member, channel, client)
        await linq.run()
