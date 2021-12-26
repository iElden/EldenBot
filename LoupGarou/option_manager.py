import nextcord

async def option_management(game, player_list):
    def check(msg):
        return msg.author == game.mj
    while True:
        em = nextcord.Embed(title="Option", description="```diff\noption:\n{}```".format(
            "\n".join("{} {} : {}".format('+' if j else '-', i, repr(j))
            for i, j in game.option.items())))
        em.set_footer(text="\"OK\" pour valider, \"{option}={valeur}\" pour modifier")
        notif = await game.channel.send(embed=em)
        message = await game.client.wait_for('message', check=check)
        await message.delete()
        if message.content == 'OK':
            em.set_footer(text="Options verrouillées")
            await notif.edit(embed=em)
            break
        av = message.content.split('=')
        if len(av) != 2:
            await game.channel.send("Syntaxe invalide\nAttendu: ``option=valeur``", delete_after=10)
            await notif.delete()
            continue
        if av[0] not in game.option:
            await game.channel.send("Syntaxe invalide\nL'option demandé n'existe pas``", delete_after=10)
            await notif.delete()
            continue
        value = av[1]
        if value.isdigit(): value = int(value)
        elif value.lower() == 'true': value = True
        elif value.lower() == 'false': value = False
        game.option[av[0]] = value
        await game.channel.send("Option modifiée o7", delete_after=10)
        await notif.delete()
    if game.option['death_channel_id']:
        game.death_channel = game.client.get_channel(game.option['death_channel_id'])