import nextcord
import asyncio
import random
from LoupGarou.decorator import are_alive

FOOT_HELP = "Entrez \">{nom de la victime}\" pour voter, tapez autres chose pour envoyer un message..."


def create_vote_msg(votes):
    max_len = max(len(i) for i in (j.name for j in votes.keys()))
    return "```diff\n{}```".format('\n'.join("{} {:{len}} > {}".format(
            '-' if v is None else '+',
            k.name,
            "Aucun" if v is None else v.name,
            len=max_len)
         for k, v in votes.items())
    )

def format_chat(chat):
    if not chat:
        return "```diff\n- [LG CHAT]\n```"
    max_len = max(len(name) for name in (m.author.name for m in chat))
    for i in range(-15, -1):
        result = "```diff\n- [LG CHAT]\n{}```".format('\n'.join(
            "{:{len}} > {}".format(
                m.name,
                m.content,
                len=max_len)
            ) for m in chat[-i:]
        )
        if len(result) > 2000:
            continue
        return result

def make_embed(votes, chatlog):
    embed = nextcord.Embed(title="Tour des loups-garous")
    embed.add_field(name="Votes", value=create_vote_msg(votes), inline=False)
    embed.add_field(name="Chat", value=format_chat(chatlog), inline=False)
    return embed

async def edit_message(msg, em):
    try:
        await msg.edit(embed=em)
    except nextcord.HTTPException:
        pass

async def edit_messages(msg_list, votes, chatlog):
    em = make_embed(votes, chatlog)
    tasks = [edit_message(msg, em) for msg in msg_list]
    await asyncio.gather(*tasks)

async def send_messages(game, member_list, content=None, embed=None):
    tasks = [member.send(content, embed=embed) for member in member_list]
    await asyncio.gather(*tasks)


@are_alive("loup-garou")
async def werewolf(game, lgs): # Game, [Player, ....]
    game.target = None
    lgs_member = [lg.member for lg in lgs] # [nextcord.Member, ...]
    votes = {i: None for i in lgs_member} # {nextcord.Member : nextcord.Member, ...}
    msg_list = [] # [nextcord.Message, ...]
    chatlog = [] # [nextcord.Message, ...]
    embed = make_embed(votes, chatlog)
    for lg in lgs:
        msg_list.append(await lg.send(embed=embed))
    while True:
        message = await game.wait_for_message(lgs_member)
        if message.content == "/lgmj skip_turn":
            return
        elif message.content.startswith('>'):
            t = game.get_player(message.content[1:].strip())
            if not t:
                await message.author.send("Joueur non trouvé", delete_after=5)
                continue
            votes[message.author] = t
            await edit_messages(lgs_member, votes, chatlog)
            if all(votes.values()):
                break
        else:
            chatlog.append(message)
            await edit_messages(lgs_member, votes, chatlog)
    l = list(votes.values())
    d = {i: l.count(i) for i in l}
    r = [k for k,v in d.items() if v == max(d.values())]
    if len(r) == 1:
        target = r[0]
        await send_messages(game, lgs_member, f"Fin du vote:\nLa cible est {target}")
    else:
        target = random.choice(r)
        await send_messages(game, lgs_member, f"Fin du vote:\nEgalité, tirage au sort ...\nLa cible est {target}")
    game.target = target
    game.add_history(f"Les loup-garous ont dévoré {game.target}")
