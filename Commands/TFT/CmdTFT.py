from util.decorator import only_owner
from .Functions import Functions
from .Database import Database
from .Team import Team

class CmdTFT:
    @only_owner
    async def cmd_tftspawnrota(self, *args, channel, **_):
        await Functions.spawn_draft(channel)

    async def cmd_tftteam(self, *args, channel, member, **_):
        with Database() as db:
            champ_list = db.get_champions(member.id)
        team = Team.from_json(champ_list, member=member)
        await channel.send(embed=team.to_embed())

    async def cmd_tftsell(self, *args, channel, member, **_):
        await Functions.sell_champ(*args, channel=channel, member=member)