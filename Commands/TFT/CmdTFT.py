from util.decorator import only_owner
from .Functions import Functions
from .Database import Database

class CmdTFT:
    @only_owner
    async def cmd_tftspawnrota(self, *args, channel, **_):
        await Functions.spawn_draft(channel)

    async def cmd_tftteam(self, *args, channel, member, **_):
        with Database() as db:
            champ_list = db.get_champions(member.id)
        await channel.send('\n'.join([f"{i['name']}: niveau {i['level']}" for i in champ_list]))