#!/usr/bin/python3
import discord
import logging
import json
import traceback

logging.basicConfig(level=logging.INFO)

from random_message import *
from Commands.link import send_to_linked
from util.function import msg
from util.exception import BotError

#Event listener
from Commands.TFT.Functions import Functions as TFT_Functions
from util.DynamicEmbed import on_reaction_change

if __name__ == '__main__':
    from Commands import Command
    command = Command()

client = discord.Client(activity=discord.Game("type /help for commands"))
logger = logging.getLogger("Main")

@client.event
async def on_ready():
    logger.info("Connected")

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    try:
        await TFT_Functions.on_champion_pick(payload, client=client)
        await on_reaction_change(payload)
    except BotError:
        error = traceback.format_exc().split('\n')[-1] or traceback.format_exc().split('\n')[-2]
        await client.get_user(payload.user_id).send(error[15:])



@client.event
async def on_message(m):
    if m.content.startswith('/') :#and m.author == client.user:
        if command.sleep and m.content != '/sleep':
            return
        member = m.author
        cmd = m.content.split(" ")[0][1:].lower()
        force = True if cmd == "force" and member.id == 384274248799223818 else False
        if force:
            cmd = m.content.split(" ")[1]
            args = m.content.split(" ")[2:]
        else: args = m.content.split(" ")[1:]
        try:
            function = getattr(command, "cmd_" + cmd)
        except:
            return
        try:
            logger.info(f"{member} used command {m.content}")
            await function(*args, message=m, member=member, force=force, cmd=cmd,
                           client=client, channel=m.channel, guild=m.guild)
        except BotError:
            error = traceback.format_exc().split('\n')[-1] or traceback.format_exc().split('\n')[-2]
            await m.channel.send(error[15:])
        except Exception:
            em = discord.Embed(title="Oh no !  😱",
                               description="Une erreur s'est produite lors de l'éxécution de la commande\n" + msg("- [FATAL ERROR]\n" + traceback.format_exc()),
                               colour=0xFF0000).set_footer(text="command : " + m.content,icon_url=m.author.avatar_url)
            await m.channel.send(embed=em)
    if m.content.startswith(f"<@{client.user.id}> play"):
        args = m.content.split(' ')[2:]
        await command.cmd_music(*args, message=m, member=m.author, force=False, cmd=None,
                                client=client, channel=m.channel, guild=m.guild)
    elif client.user in m.mentions and m.author != client.user:
        await random_message(client, m)
    await send_to_linked(client, m)


if __name__ == '__main__':
    fd = open("private/token")
    client.run(json.load(fd))
    fd.close()
