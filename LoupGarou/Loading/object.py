import nextcord
import logging

logger = logging.getLogger("LG")

class Player:
    def __init__(self, role, images, member, plid, game):
        self.life = True # Bool
        self.role = role(images) # Role
        self.member = member # nextcord.Member
        self.name = member.name # str
        self.id = plid # int
        self.love = None # unused ?
        self.game = game # Game
    def __str__(self):
        return self.name
    def __int__(self):
        return self.id
    async def kill(self, reason="none") -> nextcord.Message:
        self.life = False
        self.game.alive.remove(self)
        if self.game.death_channel:
            try : await self.member.move_to(self.game.death_channel)
            except: logger.warning("Can't move member to death_channel")
        ann = await self.game.announce('death_' + reason, author=self.member,
                                       image=self.role.image if self.game.option['show_role_at_death'] else None,
                                       desc_args={'player': self.name})
        if self.game.lovers and self in self.game.lovers:
            self.game.lovers.remove(self)
            await self.game.lovers[0].kill(reason="love")
        return ann
    async def send(self, *args, **kwargs) -> nextcord.Message:
        return await self.member.send(*args, **kwargs)

from LoupGarou.Loading.announce import load_announce
from LoupGarou.Loading.constant import OPTION

class Game:
    def __init__(self, mj, channel, client):
        self.mj = mj # nextcord.Member
        self.channel = channel # nextcord.Channel
        self.client = client # nextcord.Client
        self.option = OPTION # {str: value, ...}
        self.players = None # [Player, ...]
        self.alive = None # [Player, ...]
        self.lovers = None # [Player, Player] or None
        self.target = None # Player or None
        self.announces = load_announce(self)
        self.history = [] # [str, ...]
        self.death_channel = None # None or Discord.VoiceChannel
        self.logger = logger

    def _set_players(self, players):
        self.players = players
        self.alive = players

    async def announce(self, ann : str, **kwarg) -> nextcord.Message:
        return await self.announces[ann].send(**kwarg)

    def get_player(self, name : str) -> Player:
        if isinstance(name, nextcord.Message):
            name = name.content
        for player in self.alive:
            if name == player.name:
                return player
        return None

    def get_player_by_member(self, member) -> Player:
        for player in self.alive:
            if player.member.id == member.id:
                return player
        return None

    async def wait_for_message(self, member_list) -> nextcord.Message:
        if not isinstance(member_list, list):
            member_list = [member_list]
        def check(mmessage):
            return (mmessage.author.id in [i.id for i in member_list]
                    or (mmessage.author == self.mj and mmessage.content.startswith('/lgmj ')))
        while True:
            message = await self.client.wait_for("message", check=check)
            if message.content.startswith('/lgmj ') and message.author != self.mj:
                continue
            return message

    def add_history(self, txt, show=True):
        logger.info(txt)
        if show:
            self.history.append(txt)
