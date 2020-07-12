import discord
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("ChannelCleaner")

CHANNELS = [516418255834054671, 571736666868285455]

def message_is_not_pinned(message: discord.Message):
    return not message.pinned

async def clear_channels(channel : discord.TextChannel):
    await channel.purge(limit=None, before=datetime.now() - timedelta(hours=24), check=message_is_not_pinned)


async def routine(client : discord.Client):
    logger.debug("Runing clear routine ...")
    for channel_id in CHANNELS:
        await clear_channels(client.get_channel(channel_id))