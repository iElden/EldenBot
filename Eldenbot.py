#!/usr/local/bin/python3.10
import nextcord
import asyncio
import logging
import json
import traceback
from sys import argv

logging.basicConfig(level=logging.INFO)

from random_message import *
from Commands.link import send_to_linked
from util.function import msg
from util.exception import BotError

#Event listener
from Commands.ChannelCleaner import routine as clear_routine
from Commands.TFT.Functions import Functions as TFT_Functions
from Commands.CivFR import FFATournament
from util.DynamicEmbed import on_reaction_change as dynamicembed_reaciton_change
from Commands.DynamicVoice import DynamicVoices
from Commands.CivFR.Level import on_message as civfrlevel_on_message
from Commands.CivFR.Level import on_reaction as civfrlevel_on_reaction
from Commands.CivFR.Level import on_edit as civfrlevel_on_edit
from Commands.CivFR.Level import on_delete as civfrlevel_on_delete

if __name__ == '__main__':
    from Commands import Command
    command = Command()

client = nextcord.Client(activity=nextcord.Game("type /help for commands"), allowed_mentions=nextcord.AllowedMentions(everyone=False), intents=nextcord.Intents.all())
logger = logging.getLogger("Main")

NO_COMMANDS_SERVER = [] #[197418659067592708]

async def bot_routine():
    await client.wait_until_ready()
    if len(argv) > 1 and argv[1] == '-d':
        await client.change_presence(status=nextcord.Status.dnd, activity=nextcord.Game("In debug mode..."))
        logger.warning("Program has been lunched with -d argument, exiting bot_routine ...")
        return
    while True:
        # await TFT_Functions.routine(client=client)
        try:
            await clear_routine(client)
        except:
            pass
        await asyncio.sleep(3600)

@client.event
async def on_ready():
    logger.info(f"Connected as {client.user}")
    try:
        await FFATournament.update_leaderboard(client)
    except:
        pass

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if after.channel is not None:
            asyncio.ensure_future(DynamicVoices.on_voice_join(member, after.channel))
        if before.channel is not None:
            asyncio.ensure_future(DynamicVoices.on_voice_leave(member, before.channel))

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    try:
        await civfrlevel_on_reaction(payload, client=client)
        await (TFT_Functions.on_champion_pick(payload, client=client))
        await (dynamicembed_reaciton_change(payload))
        await (FFATournament.on_dindon(payload, client=client))
    except BotError:
        error = traceback.format_exc().split('\n')[-1] or traceback.format_exc().split('\n')[-2]
        await client.get_user(payload.user_id).send(error[15:])

@client.event
async def on_raw_message_edit(payload : nextcord.RawMessageUpdateEvent):
    await civfrlevel_on_edit(payload, client=client)

@client.event
async def on_raw_message_delete(payload : nextcord.RawMessageDeleteEvent):
    await civfrlevel_on_delete(payload, client=client)

@client.event
async def on_message(m):
    if command.sleep and m.content != '/sleep':
        return
    if m.content.startswith('/') and not m.author.bot:
        if m.guild and m.guild.id in NO_COMMANDS_SERVER:
            logger.info(f"Cancel command on NO_COMMANDS_SERVER : <{m.author}> {m.content}")
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
            await function(*(i for i in args if i), message=m, member=member, force=force, cmd=cmd,
                           client=client, channel=m.channel, guild=m.guild, content=' '.join(args))
        except BotError as e:
            await m.channel.send(f"{type(e).__name__}: {e}")
        except Exception:
            em = nextcord.Embed(title="Oh no !  😱",
                               description="Une erreur s'est produite lors de l'éxécution de la commande\n" + msg("- [FATAL ERROR]\n" + traceback.format_exc()),
                               colour=0xFF0000).set_footer(text="command : " + m.content,icon_url=m.author.avatar_url)
            await m.channel.send(embed=em)
    if m.content.startswith(f"<@{client.user.id}> play"):
        args = m.content.split(' ')[2:]
        await command.cmd_music(*args, message=m, member=m.author, force=False, cmd=None,
                                client=client, channel=m.channel, guild=m.guild, content=m.content)
    elif client.user in m.mentions and m.author != client.user:
        await random_message(client, m)
    try:
        await civfrlevel_on_message(m)
        await FFATournament.on_report(m)
    except BotError as e:
        await m.channel.send(f"{type(e).__name__}: {e}")
    except Exception:
        em = nextcord.Embed(title="Oh no !  😱",
                           description="Une erreur s'est produite lors de l'éxécution de la commande\n" + msg("- [FATAL ERROR]\n" + traceback.format_exc()),
                           colour=0xFF0000).set_footer(text="command : " + m.content,icon_url=m.author.avatar_url)
        await m.channel.send(embed=em)
    await (command.pnj_manager_on_message(m))
    await (send_to_linked(client, m))


if __name__ == '__main__':
    asyncio.ensure_future(bot_routine())
    with open("private/debug_token" if len(argv) > 1 and argv[1] == '-d' else "private/token") as fd:
        _token = fd.read()
    client.run(_token)
