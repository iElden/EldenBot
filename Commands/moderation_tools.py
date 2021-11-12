import discord
import datetime
from util.decorator import can_manage_message, only_owner
from util.exception import InvalidArgs

MOD_DELETED = ("Votre message a été supprimé par {} pour la raison suivante :"
               + "\n{}\nRappel du message :\n{}")
MOD_MOVE = ("Votre message a été déplacé de {} à {} par {} pour la raison "
            + "suivante :\n{}")

async def move_message(msg, target, reason):
    em = discord.Embed(description=msg.content, timestamp=msg.created_at)
    em.set_footer(text="message déplacé")
    em.set_author(icon_url=msg.author.avatar_url, name=msg.author.name)
    if msg.attachments:
        em.set_image(url=msg.attachments[0].url)
    await target.send(embed=em)
    await msg.delete()
    if reason:
        await msg.author.send(reason)

class CmdModeration:
    @only_owner
    async def cmd_jailaflemmedetoutbanalamain(self, *args, message : discord.Message, channel, member, **_):
        for member in message.mentions:
            try:
                if len(member.roles) != 1:
                    await channel.send(f"Error while banning {member.mention}, this member not have only 1 role")
                    continue
                await member.ban(reason="Scam bot")
                await channel.send(f"Banned {member.mention} for the following reason : Scam bot")
            except:
                pass

    @can_manage_message
    async def cmd_mdelete(self, *args, message, channel, member, **_):
        """/mdelete {message_id} [!][*raison]"""
        if not args:
            raise InvalidArgs("Pas d'argument reçu")
        msg = await channel.fetch_message(int(args[0]))
        await msg.delete()
        await message.delete()
        if len(args) >= 2:
            reason = ' '.join(args[1:])
            if reason.startswith('!'):
                await msg.author.send(MOD_DELETED.format(member.mention, reason[1:],
                                                         msg.content))

    @can_manage_message
    async def cmd_mmove(self, *args, message, member, channel, client, **_):
        """/mmove {message_id} {channel} [!][*raison]"""
        await message.delete()
        if not args:
            raise InvalidArgs("Pas d'argument reçu")
        msg = await channel.fetch_message(int(args[0]))
        target = client.get_channel(int(args[1]))
        reason = None
        if len(args) >= 3:
            reason = ' '.join(args[2:])
            if reason.startswith('!'):
                reason = MOD_MOVE.format(channel.mention, target.mention,
                                         member.mention, reason[1:])
        await move_message(msg, target, reason)

    @can_manage_message
    async def cmd_mmoveafter(self, *args, channel, member, message, client, **_):
        """/mmoveafter {message_id} {channel} [!][*raison]"""
        await message.delete()
        if not args:
            raise InvalidArgs("Pas d'argument reçu")
        msg = await channel.fetch_message(int(args[0]))
        target = client.get_channel(int(args[1]))
        reason = None
        if len(args) >= 3:
            reason = ' '.join(args[2:])
            if reason.startswith('!'):
                reason = MOD_MOVE.format(channel.mention, target.mention,
                                         member.mention, reason[1:])
        history = await channel.history(after=msg.created_at - datetime.timedelta(milliseconds=1),
                                        limit=None).flatten()
        notified = set()
        for msg in history:
            await move_message(msg, target,
                               reason if msg.author not in notified else None)
            notified.add(msg.author)
