import discord
import random
import asyncio
from util.function import get_webhook
from util.decorator import only_owner

LINK_AVATAR_URL = "https://cdn.discordapp.com/attachments/431225592189288459/645365925301977099/unknown.png"
KING_AVATAR_URL = "https://cdn.discordapp.com/attachments/431225592189288459/645366496092225567/unknown.png"
SQUALALA_AVATAR_URL = "https://cdn.discordapp.com/attachments/431225592189288459/645367239750713380/unknown.png"
ZELDA_AVATAR_URL = "https://cdn.discordapp.com/attachments/431225592189288459/645368900720132116/unknown.png"
MAGIC_CARPET_AVATAR_URL = "https://cdn.discordapp.com/attachments/431225592189288459/645369953956003850/Tapis_volant.png"

class CmdUseless:
    async def cmd_getroleid(self, *args, channel, guild, **_):
        role = discord.utils.get(guild.roles, name=' '.join(args))
        if not role:
            await channel.send("Role non trouvé")
        await channel.send(str(role.id))

    async def cmd_thanossnap(self, channel, guild, **_):
        vanished, survivors = [], []
        for user in guild.members:
            if random.randint(0, 1):
                vanished.append(user.name)
            else:
                survivors.append(user.name)
        em = discord.Embed(title="Thanos snap simulator", colour=0xF7AD43)
        em.add_field(name="the vanished", value='\n'.join(vanished))
        em.add_field(name="the survivors", value='\n'.join(survivors))
        await channel.send(embed=em)

    @only_owner
    async def cmd_ganon(self, channel, **_):
        webhook = await get_webhook(channel)
        await webhook.send("Ahhhh, qu'est ce qu'on peut s'ennuyer ici !", username="Link", avatar_url=LINK_AVATAR_URL)
        await asyncio.sleep(3)
        await webhook.send("Mon petit, cette paix est ce pourquoi luttent tous les vrais guerriers.", username="Le roi", avatar_url=KING_AVATAR_URL)
        await asyncio.sleep(5)
        await webhook.send("Je me demande ce que Ganon est en train de faire.", username="Link", avatar_url=LINK_AVATAR_URL)
        await asyncio.sleep(3)
        await webhook.send("*Wooooousssssshhhh, Shhoooooooooo*", username="Tapis  Volant", avatar_url=MAGIC_CARPET_AVATAR_URL)
        await asyncio.sleep(3)
        await webhook.send("Votre majesté, Ganon et ses fidèles se sont emparés de l'ile de Coridaïe.", username="Squalala", avatar_url=SQUALALA_AVATAR_URL)
        await asyncio.sleep(4)
        await webhook.send("Hmmmm, que pouvons nous faire ?", username="Le roi", avatar_url=KING_AVATAR_URL)
        await asyncio.sleep(2)
        await webhook.send("Il est écrit : \"Seul Link peut vaincre Ganon\" !", username="Squalala", avatar_url=SQUALALA_AVATAR_URL)
        await asyncio.sleep(5)
        await webhook.send("C'est génial ! Je prends mes affaires !", username="Link", avatar_url=LINK_AVATAR_URL)
        await asyncio.sleep(2)
        await webhook.send("Nous n'avons plus le temps ! Ton épée suffira.", username="Squalala", avatar_url=SQUALALA_AVATAR_URL)
        await asyncio.sleep(3)
        await webhook.send("Et un petit baiser pour me porter chance ?", username="Link", avatar_url=LINK_AVATAR_URL)
        await asyncio.sleep(4)
        await webhook.send("Tu veux plaisenter ?!", username="Zelda", avatar_url=ZELDA_AVATAR_URL)
        await asyncio.sleep(5)
        await webhook.send("Squalala, nous sommes parti !", username="Squalala", avatar_url=SQUALALA_AVATAR_URL)
        await asyncio.sleep(3)
        await webhook.send("*Wiiiiiissshhhh, wooooosssshhh*", username="Tapis  Volant", avatar_url=MAGIC_CARPET_AVATAR_URL)
