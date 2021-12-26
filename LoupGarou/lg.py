from LoupGarou.Loading.object import Game, Player
from LoupGarou.Loading.constant import *
from LoupGarou.Loading.announce import load_images
from LoupGarou.gameloop import game_loop
from LoupGarou.option_manager import option_management
import nextcord
import random


class CmdLg:
    async def cmd_lg(self, *args, message, member, force, client, **_):
        if args and args[0] == "start":
            await lg_start(message, args[1:], member, client)

async def lg_start(message, argv, mj, client):
    game = Game(mj, message.channel, client)
    #create players list
    players_list = await create_plist(message, mj, client)
    #option
    await option_management(game, players_list)
    #role distribution
    players = await distrib_role(players_list, game)
    game._set_players(players)
    #create game object
    await game_loop(game)


async def distrib_role(players_list, game):
    em = nextcord.Embed(title="distribution des role...", description="0/{}".format(len(players_list)))
    notif = await game.channel.send(embed=em)
    players = []
    role_list  = ROLE_LIST[:len(players_list)]
    images = load_images(game)
    plid = 0
    while players_list:
        plid += 1
        em = nextcord.Embed(title="distribution des role...", description="{}/{}".format(plid, len(players_list)))
        await notif.edit(embed=em)
        player_index = random.randint(0, len(players_list) - 1)
        role_index = random.randint(0, len(players_list) - 1)
        new_player = Player(role_list[role_index], images, players_list[player_index], plid, game)
        players.append(new_player)
        del role_list[role_index], players_list[player_index]
        await game.announce("announce_" + str(new_player.role),
                            author=new_player.member, mp=True,
                            image=new_player.role.image)
    return players

async def create_plist(message, mj, client):
    players_list = [mj]
    em = nextcord.Embed(title=START_PL_TITLE, description="")
    msg = await message.channel.send(embed=em)
    await msg.add_reaction(OK_EMOJI)

    def check(reaction, user):
        ok = str(reaction.emoji) == OK_EMOJI
        next = str(reaction.emoji) == NEXT_EMOJI
        return reaction.message.id == msg.id and (ok or next) and user != client.user

    while True:
        #update players_list
        for reaction in msg.reactions:
            if str(reaction.emoji) == OK_EMOJI:
                async for user in reaction.users():
                    if user != client.user:
                        players_list.append(user)
        em = nextcord.Embed(title=START_PL_TITLE,
                           description="\n".join(["- " + i.name for i in players_list]))
        await msg.edit(embed=em)
        reaction, user = await client.wait_for('reaction_add', check=check)
        if str(reaction.emoji) == NEXT_EMOJI and user == mj:
            break
        if len(players_list) >= 6:
            try: await msg.add_reaction(NEXT_EMOJI)
            except: pass
        if str(reaction.emoji) == OK_EMOJI and user not in players_list:
            players_list.append(user)
    em.set_footer(text="Les joueurs ont été lock")
    await msg.edit(embed=em)
    return players_list
