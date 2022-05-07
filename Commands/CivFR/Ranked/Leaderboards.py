import nextcord

from util.exception import ALEDException
from Commands.CivFR.Database import db
from Commands.CivFR.constant import SKILL

LB_FFA = {'channel_id': 949237443025051648,
          'message_id': [971815425165889536, 971815426415820810, 971815427569238056, 971815428659769424, 971815429691539497,
                         971815447194374224, 971815447781576785, 971815449232834640, 971815450537259048, 971815451959128084]}

class CmdLeaderboards:
    async def update_leaderboard(self, client):
        players = db.get_all_s1_players_stats(min_games=3)
        channel = client.get_channel(LB_FFA['channel_id'])
        if not channel:
            raise ALEDException(
                f"Can't find channel ID {LB_FFA['channel_id']} for the Leaderboard")
        players.sort(key=lambda pl_: SKILL(pl_.get_rating()), reverse=True)
        txt = "`Place Points [wins - loss]  win%  1er`\n"
        for j, msg_id in enumerate(LB_FFA['message_id']):
            msg: nextcord.PartialMessage = channel.get_partial_message(msg_id)
            for i in range(j * 10, (j + 1) * 10):
                if i >= len(players):
                    txt += f"`#{i + 1:<3}      -  [     -     ]     -    -`\n"
                else:
                    pl = players[i]
                    txt += f"`#{i + 1:<3}  {int(SKILL(pl.get_rating())):>5}  [ {pl.wins:>3} - {pl.games - pl.wins:<3} ]  {pl.wins / pl.games:4.0%}  {pl.first:>3}` <@{pl.id}>\n"
            await msg.edit(content=txt)
            txt = ""


    async def cmd_force_update_leaderboard(self, *args, client, **_):
        await self.update_leaderboard(client)