import nextcord
from typing import List, Tuple, Dict

from .views.ReportView import RankedView

from Commands.CivFR.Voting import Voting, RANKED_SETTINGS
from Commands.CivFR.constant import CIVFR_GUILD_ID
from Commands.CivFR.utils import is_arbitre
from constant import emoji
from util.exception import ALEDException

RANKED_CHANNEL = 507906776461475841
ADMIN_USERS = []
ADMIN_ROLES = []

TMP_MSG_TO_GR = {}

CIVFR_GUILD_ID = 500383456245579777

async def on_reaction(payload : nextcord.RawReactionActionEvent, *, client : nextcord.Client):
    if payload.channel_id != RANKED_CHANNEL:
        return
    civfr: nextcord.Guild = client.get_guild(CIVFR_GUILD_ID)
    member : nextcord.Member = civfr.get_member(payload.user_id)
    if not member:
        raise ALEDException("Member not found on CivFR")
    # if not is_arbitre(member, client=client):
    #     return
    print(f"Hello {payload.emoji} {payload.emoji == emoji.DRAGON}")
    if str(payload.emoji) == emoji.DRAGON:
        channel = client.get_channel(payload.channel_id)
        msg = channel.get_partial_message(payload.message_id)
        await msg.edit(view=RankedView(TMP_MSG_TO_GR[msg.id], parent=msg, client=client))

class RankedReport:
    def __init__(self, players : List[nextcord.Member], host : nextcord.Member):
        self.players : List[int] = players
        self.admin_roles = ADMIN_ROLES
        self.admin_users = ADMIN_USERS + [host.id]
        self.players_pos : Dict[int, int] = {k: None for k in self.players} # {player_id: position}

    async def post(self, client : nextcord.Client):
        channel = client.get_channel(RANKED_CHANNEL)
        msg = await channel.send(embed=self.get_embed())
        for i in range(1, len(self.players)+1):
            await msg.add_reaction(emoji.NB[i])
        await msg.add_reaction(emoji.DRAGON)
        TMP_MSG_TO_GR[msg.id] = self

    def get_embed(self) -> nextcord.Embed:
        desc = ""
        for i in range(1, len(self.players)+1):
            desc += f"\n``{i:>2}:``" + ' ,'.join(f"<@{pl}>" for pl in self.players if self.players_pos[pl] == i)
        pl_waiting = [k for k, v in self.players_pos.items() if v is None]
        if pl_waiting:
            desc += "\n\nEn attente de pointage: " + ', '.join(f"<@{pl}>" for pl in pl_waiting)
        em = nextcord.Embed(title="Ranked Report", description=desc)
        return em

    def set_player_position(self, player_id, position):
        self.players_pos[player_id] = position


class RankedGame:
    def __init__(self):
        self.vote = None
        self.ranked_report : RankedReport = None

    async def run(self, channel, member, client):
        vote = Voting([], RANKED_SETTINGS)
        # await vote.run(channel, client)
        report = RankedReport([111335315238641664, 186417692960358401, 143088067337650176, 146222256325001216], member)
        await report.post(client)


class CmdCivFRRanked:
    async def cmd_startranked(self, *args, channel, client, member, **_):
        rg = RankedGame()
        await rg.run(channel, member, client)

