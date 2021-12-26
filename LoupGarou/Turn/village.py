import nextcord
import asyncio

def create_vote_msg(votes, max_len):
    return "```diff\nVote du village :\n{}```\nTapez ``vote {{player}}`` pour voter\n{}".format(
        '\n'.join(["{} {:{len}} -> {}".format(
            '+' if v else '-',
            k,
            v,
            len=max_len
        ) for k, v in votes.items()]),
        "Egalité, le vote sera terminé que quand il y aura majorité ..." if all(votes.values()) else "",)

async def village(game):
    players = game.alive # [Player, ...]
    votes = {i.member: None for i in players} # {nextcord.Member : nextcord.Member, ...}
    _voted = [] # [nextcord.Member, ...]
    _max_vote = 0
    target = [] # in while : [nextcord.Member, ...] / after : nextcord.Member
    max_len = max([len(i.name) for i in players])

    if len(players) == 2:
        await game.channel.send("Il n'y a pas assez d'habitant pour voter ...")
        return
    msg = await game.channel.send(create_vote_msg(votes, max_len))
    while not all(votes.values()) or len(target) != 1:
        message = game.wait_for_message(players)
        target = game.get_player(message.content)
        if not target:
            asyncio.create_task(message.channel.send("Joueur non trouvé", delete_after=10))
            continue
        votes[message.author] = target
        asyncio.create_task(msg.edit(create_vote_msg(votes, max_len)))
        if all(votes.values()):
            _voted = list(votes.values())
            _max_vote = max([_voted.count(i) for i in _voted])
            target = [i for i in _voted if _voted.count(i) == _max_vote]
    await game.get_player_by_member(target[0]).kill(reason="village")
    game.add_history(f"Le village a tué {target[0]} ({target[0].role})")