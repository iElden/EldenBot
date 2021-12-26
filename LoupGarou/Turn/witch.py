from LoupGarou.decorator import is_alive
import nextcord

@is_alive("sorcière")
async def witch(game, player):
    em = nextcord.Embed(title="Sorcière")
    em.add_field(name='Potion disponible', value="```diff\n{} Potion de soin: {}\n{} Potion de poison: {}".format(
        '+' if player.role.heal else '-',
        player.role.heal,
        '+' if player.role.poison else '-',
        player.role.poison
    ))
    em.add_field(name='Commande',
                 value="Tapez:\n"
                       + ("``heal`` pour soigner la victime" if player.role.heal else "")
                       + ("``kill {player}`` pour empoissoner un joueur" if player.role.poison else "")
                       + "\n``end`` pour finir votre tour")
    await player.send(embed=em)
    while True:
        if not player.role.poison and not player.role.heal:
            break
        message = game.wait_for_message(player)
        cmd, av = message.content.split(' ')[0].lower(), ' '.join(message.content.split(' ')[1:])
        if cmd == 'end':
            break
        if cmd == 'heal':
            if not game.target:
                await player.send("Il n'y a pas de victime", after_delete=15)
            elif not player.role.heal:
                await player.send("Vous n'avez plus de potion de soin ...", after_delete=15)
            else:
                await player.send(f"Vous trouvez {game.target} évanouie, vous versez votre solution de soin pour l'éviter de succomber à ses blessures")
                player.role.heal -= 1
                await game.target.send("Vous étiez la victime des loups-garou, mais la sorcière vous a sauvé")
                game.add_history(f"La sorcière ({player}) a sauvé {game.target.role}")
                game.target = None
        if cmd == 'kill':
            tget = game.get_player(av)
            if not player.role.poison:
                await player.send("Vous n'avez plus de potion de poison ...", after_delete=15)
            elif not tget:
                await player.send("Joueur non trouvé ...", after_delete=15)
            else:
                await player.send(f"Vous vous introduisez dans la maison de {tget} et versez un peu de poison dans sa bouche ... c'est très efficace")
                player.role.poison -= 1
                await tget.kill(reason="sorcière")
                game.add_history(f"La sorcière ({player}) a tué {tget} ({tget.role})")