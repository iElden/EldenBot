from util.function import get_member_in_channel
from util.exception import NotFound


class CmdUtility:
    async def cmd_pingvocal(self, *args, channel, member, **_):
        members = get_member_in_channel(member.voice)
        if not members:
            raise NotFound("Member not found in channels")
        await channel.send(' '.join(member.mention for member in members))