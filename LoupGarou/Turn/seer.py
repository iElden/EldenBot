from LoupGarou.decorator import is_alive
import nextcord

@is_alive("voyante")
async def seer(game, player):
    check = lambda message: message.author == player.member

    em = nextcord.Embed(title="Joueur en vie",
                       description='\n'.join(
                            ['- ' + i.name for i in game.alive if i != player]
                      ))
    em.set_footer(text="Entrez le nom de la cible dans le chat")
    await player.send(embed=em)
    target = None
    while not target:
        inp = await game.client.wait_for('message', check=check)
        target = game.get_player(inp)
        if not target :
            await player.send("Joueur introuvable")
    await game.announce("voyante_" + target.role.name, mp=True,
                        author=player.member, image=target.role.image)
    game.add_history(f"La voyante ({player}) a révélé l'identité de {target} ({target.role})")
