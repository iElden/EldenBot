import discord
from .constant import ARBITRE_ID, CIVFR_GUILD_ID
from util.exception import ALEDException

def is_arbitre(member : discord.Member, client=None):
    if member.guild is None:
        if client is None:
            raise ALEDException("Client not given for checking if the member is Arbitre")
        member = client.get_guild(CIVFR_GUILD_ID)
    return ARBITRE_ID in [role.id for role in member.roles]

def is_civfr_guild_or_mp(channel):
    return channel.guild.id == CIVFR_GUILD_ID or isinstance(channel, discord.DMChannel)