import nextcord

REGEX = {
    rf"<@{client.user.id}> play"
}


async def easter_egg(message) -> bool:
    """
    :type message: nextcord.Message
    :rtype: bool
    """
