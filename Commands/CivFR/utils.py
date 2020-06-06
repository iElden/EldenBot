import discord
from .constant import ARBITRE_ID

def is_arbitre(member : discord.Member):
    return ARBITRE_ID in [role.id for role in member.roles]