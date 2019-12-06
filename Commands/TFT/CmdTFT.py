from util.decorator import only_owner
from .Functions import Functions

class CmdTFT:
    @only_owner
    async def cmd_tftspawnrota(self, *args, channel, **_):
        await Functions.spawn_draft(channel)