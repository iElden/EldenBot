import discord
import re
import json
from util.exception import ALEDException

WEBHOOK_NAME = "EldenBotWook"

def msg(message, error=False):
    if error : return("```diff\n- [ERREUR]\n{}```".format(message))
    else :     return("```diff\n{}```".format(message))
    
def get_channel_named(server, name):
    return(discord.utils.get(server.channels, name=name))

def get_role_id(server, role_id):
    for i in server.roles:
        if i.id == role_id : return(i)
    return(None)

def get_role_named(server, name):
    for i in server.roles:
        if i.name == name : return(i)
    return(None)

def get_member(guild, name):
    member = guild.get_member_named(name)
    if member:
        return member
    match = re.findall(r"<@!?(\d+)>", name)
    if match:
        return guild.get_member(int(match[0]))
    if name.isdigit():
        return guild.get_member(int(name))
    return None

def load_json_file(file):
    try:
        with open(file, 'r') as fd:
            return json.loads(fd.read())
    except:
        raise ALEDException(f"Impossible de lire le fichier {file}, le fichier a soit été déplacé, supprimé ou comrompu !")

def write_json_file(file, obj):
    try:
        with open(file, 'w') as fd:
            json.dump(obj, fd)
    except:
        raise ALEDException(f"Impossible d'écrire le fichier {file} !")

async def get_webhook(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == WEBHOOK_NAME:
            return webhook
    webhook = await channel.create_webhook(name=WEBHOOK_NAME)
    return webhook