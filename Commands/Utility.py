from util.function import get_member_in_channel
from util.exception import NotFound, InvalidArgs

import random

class CmdUtility:
    async def cmd_pingvocal(self, *args, channel, member, **_):
        members = get_member_in_channel(member.voice)
        if not members:
            raise NotFound("Member not found in channels")
        await channel.send(' '.join(member.mention for member in members))

    async def cmd_randomgroup(self, *args, channel, member, client, **_):
        if len(args) >= 2:
            if not args[1].isdigit():
                raise InvalidArgs("2nd Argument must be a channel ID")
            target = client.get_channel(int(args[1]))
            if not target:
                raise NotFound(f"Channel ID {args[1]} not found")
        else:
            if not member.voice or not member.voice.channel:
                raise NotFound("Impossible de récupérer les joueurs : Vous n'êtes pas connecté à un channel vocal")
            target = member.voice.channel
        members = target.members
        if not members:
            raise NotFound("Member not found in channels")
        if not args:
            raise InvalidArgs("Invalid syntax: `/randomgroup {number_of_group}`")
        if not args[0].isdigit():
            raise InvalidArgs("1st Argument must be a number")
        random.shuffle(members)
        nb = int(args[0])
        groups = []
        div, mod = divmod(len(members), nb)
        x = 0
        for i in range(nb):
            y = div+(i<mod)
            await channel.send(f"`group {i+1}`: {', '.join(f'<@{i.id}>' for i in members[x:x+y])}")
            x += y
