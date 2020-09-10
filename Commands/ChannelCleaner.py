import discord
import logging
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger("ChannelCleaner")

CHANNELS : Dict[int, timedelta] = {
    516418255834054671: timedelta(hours=24),
    571736666868285455: timedelta(days=30)
}

def message_is_not_pinned(message: discord.Message):
    return not message.pinned

async def clear_channels(channel : discord.TextChannel, delta : timedelta):
    await channel.purge(limit=None, before=datetime.now() - delta, check=message_is_not_pinned)


async def routine(client : discord.Client):
    logger.debug("Runing clear routine ...")
    for channel_id, delta in CHANNELS.items():
        await clear_channels(client.get_channel(channel_id), delta)
