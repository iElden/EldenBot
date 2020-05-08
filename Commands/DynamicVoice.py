import re
import asyncio

class DynamicVoices:
    CHANNEL_CREATORS = [708405584298377226]
    channels = []

    @classmethod
    async def on_voice_leave(cls, member, channel):
        if channel.id in cls.channels and not channel.members:
            await channel.delete(reason="No member connected to tmp channel")

    @classmethod
    async def on_voice_join(cls, member, channel):
        if channel.id in cls.CHANNEL_CREATORS:
            await DynamicVoices.create(member, channel)

    @classmethod
    async def create(cls, member, channel):
        # WARNING: The channel.position attribute is very full drunk !
        # -------: Don't ask me why, but discord API is really dump
        if not channel.category:
            return

        pos = channel.category.channels.index(channel) # For fixing discord API false information
        last_channel = channel.category.channels[pos - 1]
        r = re.search(r"(\d+)$", last_channel.name)
        nb = int(r[0]) + 1 if r else '?'
        new_channel = await channel.category.create_voice_channel(f"🎮 Public #{nb}", user_limit=99)
        cls.channels.append(new_channel.id)
        asyncio.ensure_future(member.move_to(new_channel))
        position = channel.position
        await new_channel.edit(position=position)





class CmdDynamicVoice:
    async def cmd_dynamicvoice(self, **_):
        ...
