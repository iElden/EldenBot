from datetime import datetime
from util.function import get_member
from util.exception import NotFound
import discord

def format_time(x):
    return x.strftime("**%a %d %B %Y - %H:%M:%S** (UTC)")

class CmdInfos:
    async def cmd_memberinfo(self, *args, member, channel, guild, **_):
        if args:
            member = get_member(guild, ' '.join(args))
            if not member:
                raise NotFound("Membre non trouvé :(")
        em = discord.Embed(title=member.display_name, colour=member.colour)
        em.add_field(name="Nom", value=member.name)
        em.add_field(name="Discriminator", value="#" + member.discriminator)
        em.add_field(name="ID", value=str(member.id))
        if member.id in [384274248799223818, 427867039135432714, 244453201036836864, 221290866717884417]:
            em.add_field(name="Type", value="Dragon")
        else:
            em.add_field(name="Type", value="Robot" if member.bot else "Humain")
        em.add_field(name="Status", value=str(member.status))
        em.add_field(name="Couleur", value=str(member.colour))
        em.add_field(name="Jeu", value=(lambda x: str(x) if x else "Aucun")(member.activity))
        if len(member.roles) > 1:
            em.add_field(name="Roles", value=', '.join([f"<@&{i.id}>" for i in reversed(member.roles) if i.id != guild.id]))
        else:
            em.add_field(name="Roles", value='Aucun')
        em.add_field(name="Serveur rejoint", value=format_time(member.joined_at), inline=False)
        em.add_field(name="Compte créé", value=format_time(member.created_at))
        # p = await member.profile()
        # badge = {"Staff": p.staff, "Partenaire": p.partner, "Bug Hunter": p.bug_hunter,
        #          "Nitro": p.nitro, "Early Supporter": p.early_supporter, "Hypesquad": p.hypesquad,
        #          "House of Brillance": p.hypesquad_houses.brilliance, "House of Balance": p.hypesquad_houses.brilliance,
        #          "House of Bravery": p.hypesquad_houses.bravery}
        # user_badge = [k for k, v in badge.items() if v]
        # if user_badge:
        #     em.add_field(name="Badges", value=format_time(member.created_at), inline=False)
        em.set_image(url=member.avatar_url)
        await channel.send(embed=em)
