import json
import discord
import logging
from random_message import *
from util.decorator import only_owner
from util.function import get_webhook

logger = logging.getLogger("Link")

def load_link_file():
    try:
        with open("private/link.data", 'r') as fd:
            return json.loads(fd.read())
    except:
        logger.error("IMPOSSBILE DE LOAD LE FICHIER private/link.data !")
        return {}

def save_link_file(data):
    with open("private/link.data", 'w') as fd:
        fd.write(json.dumps(data))

linked = load_link_file() #format = {channel_id : [channel_id, ...], ...}

async def show(message):
    txt = "Salons liés:\n"
    for c, l in linked.items():
        if l: txt += "<#{}> -> {}\n".format(c, ", ".join(["<#{}>".format(i) for i in l]))
    await message.channel.send(txt)

async def add(message, args):
    channel_id = int(args[1])
    if channel_id not in linked.keys():
        linked[str(channel_id)] = []
    linked[str(channel_id)].append(message.channel.id)
    if len(args) <= 2 or args[2] != "uni":
        if message.channel.id not in linked.keys():
            linked[str(message.channel.id)] = []
        linked[str(message.channel.id)].append(channel_id)
    save_link_file(linked)

async def delete(message, args):
    deleted = []
    if len(args) == 1:
        for i in linked[str(message.channel.id)]:
            try:
                linked[str(i)].remove(message.channel.id)
                deleted.append((i, message.channel.id))
                if not linked[str(i)]: del linked[str(i)]
            except:
                pass
        await message.channel.send("Link détruit : {}".format(
            "\n".join(["<#{}> -> <#{}>".format(i, j) for i,j in deleted] +
                      ["<#{}> -> <#{}>".format(
                          message.channel.id, i) for i in linked[str(message.channel.id)]])))
        del linked[str(message.channel.id)]
    else:
        try:
            linked[str(message.channel.id)].remove(int(args[1]))
            await message.channel.send("<#{}> -> <#{}>".format(message.channel.id, args[1]))
        except:
            pass
        try:
            linked[args[1]].remove(message.channel.id)
            await message.channel.send("<#{}> -> <#{}>".format(args[1], message.channel.id))
        except:
            pass
        await message.channel.send("")
    save_link_file(linked)


async def send_to_linked(client, message):
    if str(message.channel.id) in linked.keys() and not message.webhook_id:
        txt = message.content
        try:
            if message.attachments:
                txt += "\n\n" + message.attachments.url
        except Exception as e:
            logger.warning(f"{e.__class__.__name__}: {e}")
        for channel in linked[str(message.channel.id)]:
            try:
                webhook = await get_webhook(client.get_channel(channel))
                await webhook.send(txt,
                                   username=f"{message.author.name} (from {message.guild.name})",
                                   avatar_url=message.author.avatar_url)
            except Exception as e:
                logger.error(f"{e.__class__.__name__}: {e}")

class CmdLink:
    @only_owner
    async def cmd_link(self, *args, message, member, **_):
        if args[0] == "show"  : await show(message)
        if args[0] == "add"   : await add(message, args)
        if args[0] == "delete": await delete(message, args)
