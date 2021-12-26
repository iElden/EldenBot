#!/usr/bin/python3
from flask import Flask, request
from pantheon import pantheon
import threading
import time
import nextcord
import asyncio
import logging
import traceback
import json

with open("../private/rgapikey") as key:
    panth = pantheon.Pantheon("euw1", key.read(), True)
    
def load_data():
    try:
        print("loading data ...")
        with open("../private/circus.data", 'r') as fd:
            data = json.loads(fd.read())
    except:
        print("IMPOSSIBLE DE LOAD ../private/circus.data")
        data = {}
    try:
        print("loading summoners ...")
        with open("../private/summoners.data", 'r') as fd:
            summ = json.loads(fd.read())
    except:
        print("IMPOSSIBLE DE LOAD ../private/summoners.data")
        summ = {}
    return (data, summ)

logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()
client = nextcord.Client()
app = Flask(__name__)
data, summoners = load_data()
start_msg = None
FORUM_GUILD_ID = 367683573014069249
CIRCUS_GUILD_ID = 466950374243303434
REG_CHANNEL_ID = 466961756393046017
LINK_CHANNEL_ID = 474254945764376577
MSG_ID = 474227467414929420
ALREADY_VERIFIED = "{} est déjà vérifié sur le discord du forum (SummonerId : {})"
FORBIDDEN = "Désolé, seuls les Organisateurs peuvent utiliser cette commande."
MISSING_ARG = "Erreur : Argument manquant"
NOT_FOUND = "Membre non trouvé"
FORCE_REGISTED = "{} a été inscrit de force à l'évenement {} par {}"
FORCE_UNREGISTED = "{} a été désinscrit de force à l'évenement {} par {}"
PRE_REGISTED = "{} a été préinscrit à l'évenement {} par {}"
REREGISTED = "{} s'est fait reregister sur l'évenement {}"
READYCHECK = "__**Vérification de présence !**__\n\nprésent: {}\nabsent: {}\n\ntemps restant: {}"
def TIME(x): return ("{}:{}".format(int(x) // 60, str(int(x) % 60).zfill(2)))
def MENTION(discord_id): return ("<@{}>".format(discord_id))


class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        app.run(port=80)

@app.route('/rgapicallback', methods=['POST'])
def rgapicallback():
    #loop = asyncio.get_event_loop()
    dic = request.data
    dic = json.loads(dic)
    try:
        loop.run_until_complete(game_ended(dic["shortCode"]))
    except RuntimeError:
        pass

async def game_ended(tournamentCode):
    channel = client.get_channel(476382883364208670)
    await channel.send("Game terminé ! (" + tournamentCode + ")")

@client.event
async def on_ready():
    print("Connected (cirque de l'invocateur)")
    await update_msg()
    ServerThread().start()
    for member in client.get_guild(CIRCUS_GUILD_ID).members:
        await verif(member)

@client.event
async def on_member_join(member):
    if member.guild.id == CIRCUS_GUILD_ID:
        await verif(member)


def get_event(emoji):
    for event_name, dic in data.items():
        if dic["emoji"] == emoji:
            return event_name
    return None
        
@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == MSG_ID:
        member = client.get_guild(CIRCUS_GUILD_ID).get_member(payload.user_id)
        event_name = get_event(payload.emoji) #return None if no event was found
        if event_name:
            await do_register(client.channel(REG_CHANNEL_ID), member, event_name)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.message_id == MSG_ID:
        member = client.get_guild(CIRCUS_GUILD_ID).get_member(payload.user_id)
        event_name = get_event(payload.emoji) #return None if no event was found
        if event_name:
            await do_unregister(client.channel(REG_CHANNEL_ID), member, event_name)


async def verif(member):
    forum = client.get_guild(FORUM_GUILD_ID)
    lie = nextcord.utils.get(member.guild.roles, id=474254455194517504)
    if lie not in member.roles:
        fmember = forum.get_member(member.id)
        if "Vérifié" in [role.name for role in fmember.roles]:
            data = await panth.getSummonerByName(fmember.display_name)
            name, summId = data['name'], data['id']
            summoners[str(member.id)] = summId
            link_channel = client.get_channel(LINK_CHANNEL_ID)
            try:
                await member.edit(nick=name)
            except nextcord.errors.Forbidden:
                pass
            await member.add_roles(lie, reason="Vérifié sur le discord du forum")
            await link_channel.send(ALREADY_VERIFIED.format(str(member), summId))
            save_summ()
    else:
        data = await panth.getSummonerByName(member.display_name)
        try:
            await member.edit(nick=data["name"])
        except:
            pass

@client.event
async def on_message(message):
    if message.guild.id == CIRCUS_GUILD_ID:
        try:
            if message.channel.id == LINK_CHANNEL_ID and \
               "Lié" not in [x.name for x in message.guild.roles]:
                pass
            if message.content.startswith('+') and message.channel.id == REG_CHANNEL_ID:
                await register(message)
            if message.content.startswith('-') and message.channel.id == REG_CHANNEL_ID:
                await unregister(message)
            if message.content.startswith('/'):
                av = message.content.split(' ')
                while '' in av : av.remove('')
                if av[0] == "/start" : await start_game(message, av)
                if av[0] == "/create" : await create(message, av)
                if av[0] == "/delete" : await delete(message, av)
                if av[0] == "/preregister" : await pre_register(message, av)
                if av[0] == "/unpreregister" : await unpre_register(message, av)
                if av[0] == "/reregister" : await reregister(message, av)
                if av[0] == "/forceregister" : await force_register(message, av)
                if av[0] == "/forceunregister" : await force_unregister(message, av)
                if av[0] == "/close" : await change_close_status(message, av, True)
                if av[0] == "/open" : await change_close_status(message, av, False)
                if av[0] == "/hide" : await change_hidden_status(message, av, True)
                if av[0] == "/show" : await change_hidden_status(message, av, False)
                if av[0] == "/emoji" : await change_event_icon(message, av)
                if av[0] == "/description" : await change_event_description(message, av)
        except Exception:
            await message.channel.send("```diff\n-[Erreur]\n" + traceback.format_exc() + "```")


def authorised(func):
    async def wrapper(message, *args, **kwargs):
        perm = message.author.guild_permissions
        if perm.administrator or perm.manage_channels or perm.manage_guild:
            await func(message, *args, **kwargs)
        else:
            await message.channel.send(FORBIDDEN, delete_after=10)
    return wrapper

async def event_exist(channel, event_name):
    if event_name not in data.keys():
        await channel.send("L'évenement n'existe pas.", delete_after=60)
        return False
    return True

async def do_register(channel, member, event_name):
    if not await event_exist(channel, event_name):
        return False
    discord_id = member.id
    if discord_id in data[event_name]["registed"]:
        await channel.send("Vous êtes déjà inscrit.", delete_after=60)
        return False
    if data[event_name]["close"]:
        await channel.send("Les inscriptions sont fermées", delete_after=60)
        return False
    data[event_name]["registed"].append(discord_id)
    await channel.send("{} s'est inscrit à l'évenement {}".format(
        MENTION(discord_id), event_name.capitalize()),
                               detele_after=60)
    await update_msg()

async def do_unregister(channel, member, event_name):
    if not await event_exist(channel, event_name):
        return False
    discord_id = member.id
    if discord_id not in data[event_name]["registed"]:
        await channel.send("Vous êtes déjà désinscrit.", delete_after=60)
        return False
    data[event_name]["registed"].remove(discord_id)
    await channel.send("{} s'est désinscrit à l'évenement {}".format(
        MENTION(discord_id), event_name.capitalize()), delete_after=60)
    await update_msg()


async def register(message):
    await message.delete()
    event_name = message.content.split('+')[1].lower()
    await do_register(message.channel, message.author, event_name)

    
async def unregister(message):
    await message.delete()
    event_name = message.content.split('-')[1].lower()
    await do_unregister(message.channel, message.author, event_name)

@authorised
async def pre_register(message, av):
    if len(av) < 3:
        await message.channel.send(MISSING_ARG)
        return False
    name = av[1]
    event_name = av[2].lower()
    if not await event_exist(channel, event_name):
        return False
    if name in data[event_name]["registed"]:
        await message.channel.send("Le membre est déjà préinscrit", delete_after=60)
        return False
    data[event_name]["registed"].append(name)
    await message.channel.send(PRE_REGISTED.format(name,
                                                   event_name.capitalize(),
                                                   message.author.mention),
                               delete_after=60)
    await update_msg()
    await message.delete()

@authorised
async def reregister(message, av):
    if len(av) < 3:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    name = av[1]
    discord_id = get_member_id(message, av[2])
    if not discord_id:
        await message.channel.send(NOT_FOUND, delete_after=60)
        return False
    for event, dic in data.items():
        for i in range(len(dic["registed"])):
            if dic["registed"][i] == name:
                dic["registed"][i] = discord_id
                await message.channel.send(REREGISTED.format(name,
                                                             event.capitalize()),
                                           delete_after=60)

@authorised
async def unpre_register(message, av):
    if len(av) < 3:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    name = av[1]
    event_name = av[2].lower()
    if not await event_exist(channel, event_name):
        return False
    if name not in data[event_name]["registed"]:
        await message.channel.send("Le membre est déjà préinscrit", delete_after=60)
        return False
    data[event_name]["registed"].remove(name)
    await message.channel.send(FORCE_UNREGISTED.format(name,
                                                       event_name.capitalize(),
                                                       message.author.mention),
                               delete_after=60)
    await update_msg()
    await message.delete()

@authorised
async def change_hidden_status(message, av, status):
    if len(av) < 2:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    event_name = av[1].lower()
    if not await event_exist(channel, event_name):
        return False
    data[event_name]["hidden"] = status
    if status : del_all_reactions(data[event_name]["emoji"])


@authorised
async def change_close_status(message, av, status):
    if len(av) < 2:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    event_name = av[1].lower()
    if not await event_exist(channel, event_name):
        return False
    data[event_name]["close"] = status
    if status : del_all_reactions(data[event_name]["emoji"])

@authorised
async def change_event_icon(message, av):
    if len(av) < 2:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    event_name = av[1].lower()
    if not await event_exist(channel, event_name):
        return False
    data[event_name]["emoji"] = av[2]


@authorised
async def change_event_description(message, av):
    if len(av) < 2:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    event_name = av[1].lower()
    if not await event_exist(channel, event_name):
        return False
    data[event_name]["description"] = " ".join(av[2:])
    
    
def get_member_id(message, txt):
    try:
        id = int(txt)
        return (id)
    except:
        try:
            member = message.guild.get_member_named(txt)
            return (member.id)
        except:
            return None

@authorised    
async def force_register(message, av):
    if len(av) < 3:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    discord_id = get_member_id(message, av[1])
    if not discord_id:
        await message.channel.send(NOT_FOUND, delete_after=60)
        return False
    event_name = av[2].lower()
    if not await event_exist(channel, event_name):
        return False
    if discord_id in data[event_name]["registed"]:
        await message.channel.send("Le membre est déjà inscrit", delete_after=60)
        return False
    data[event_name]["registed"].append(discord_id)
    await message.channel.send(FORCE_REGISTED.format(MENTION(discord_id),
                                                     event_name.capitalize(),
                                                     message.author.mention), delete_after=60)
    await update_msg()
    await message.delete()

@authorised
async def force_unregister(message, av):
    if len(av) < 3:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    discord_id = get_member_id(message, av[1])
    if not discord_id:
        await message.channel.send(NOT_FOUND, delete_after=60)
        return False
    event_name = av[2].lower()
    if not await event_exist(channel, event_name):
        return False
    if discord_id not in data[event_name]["registed"]:
        await message.channel.send("Le membre est déjà désinscrit", delete_after=60)
        return False
    data[event_name]["registed"].remove(discord_id)
    await message.channel.send(FORCE_UNREGISTED.format(MENTION(discord_id),
                                                       event_name.capitalize(),
                                                       message.author.mention), delete_after=60)
    await update_msg()
    await message.delete()
    
@authorised    
async def create(message, av):
    if len(av) < 3:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    event_name = av[1].lower()
    if event_name in data.keys():
        await message.channel.send("L'évenement existe déjà.", delete_after=60)
        return False
    data[event_name] = {}
    data[event_name]["registed"] = []
    data[event_name]["close"] = False
    data[event_name]["hidden"] = False
    data[event_name]["emoji"] = av[2]
    data[event_name]["description"] = " ".join(av[3:]) if len(av) > 3 else None
    data[event_name]["timestamp"] = None
    await add_reaction(data[event_name]["emoji"])
    await update_msg()
    await message.channel.send("evenement ajouté", delete_after=60)
    await message.delete()


@authorised
async def delete(message, av):
    if len(av) < 2:
        await message.channel.send(MISSING_ARG, delete_after=60)
        return False
    event_name = av[1].lower()
    if not await event_exist(channel, event_name):
        return False
    await del_all_reactions(data[event_name]["emoji"])
    del data[event_name]
    await update_msg()
    await message.channel.send("evenement supprimé", delete_after=60)
    await message.delete()

    
async def update_msg():
    save_data()
    channel = client.get_channel(REG_CHANNEL_ID)
    msg = await channel.fetch_message(MSG_ID)
    txt = "__Liste des inscrits__:\n\n"
    for event, dic in data.items():
        if not dic["hidden"]:
            txt += "__**{}**__:\n{}inscrits {}: {}\n\n".format(
                event.capitalize(),
                (dic["description"] + '\n') if dic["description"] else "",
                "(fermé) " if dic["close"] else "",
                ", ".join([MENTION(i) if str(i).isdigit() else i for i in dic["registed"]]))
    await msg.edit(content=txt)

@authorised
async def start_game(message, av):
    global start_msg
    await message.delete()
    channel = client.get_channel(REG_CHANNEL_ID)
    game = av[1].lower()
    timer = time.time() + (360 if len(av) == 2 else int(av[2]))
    pl = data[game]["registed"]
    start_msg = await message.channel.send(
        READYCHECK.format("",
                          ", ".join([MENTION(i) for i in pl]),
                          TIME(timer - time.time())))
    await start_msg.add_reaction("✔")
    while timer - time.time() >= 0 :
        try:
            start_msg = await channel.fetch_message(start_msg.id)
            ready = await start_msg.reactions[0].users().flatten()
            ready = [i.id for i in ready]
            await start_msg.edit(content=\
                READYCHECK.format(", ".join([MENTION(i) for i in pl if i in ready]),
                                  ", ".join([MENTION(i) for i in pl if i not in ready]),
                                  TIME(timer - time.time())))
        except:
            pass
        await asyncio.sleep(0.5)
    print("done")

async def del_all_reactions(emoji):
    channel = client.get_channel(REG_CHANNEL_ID)
    msg = await channel.fetch_message(MSG_ID)
    for reaction in reactions:
        if reaction.emoji == emoji:
            async for user in reaction.users():
                await msg.remove_reaction(emoji, user)
    
def save_data():
    with open("../private/circus.data", 'w') as fd:
        fd.write(json.dumps(data))

def save_summ():
    with open("../private/summoners.data", 'w') as fd:
        fd.write(json.dumps(summoners))

with open("../private/token") as fd:
    client.run(json.load(fd))
