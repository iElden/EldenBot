import nextcord
import datetime
from util.decorator import can_manage_message, only_owner
from util.exception import InvalidArgs

from typing import List

MOD_DELETED = ("Votre message a été supprimé par {} pour la raison suivante :"
               + "\n{}\nRappel du message :\n{}")
MOD_MOVE = ("Votre message a été déplacé de {} à {} par {} pour la raison "
            + "suivante :\n{}")
SCAM_BOT = "Vous avez été banni car votre profil a été detecté comme un bot, si ce n'est pas le cas, contactez le twitter CivFR pour faire deban votre compte: https://twitter.com/civfr"

async def move_message(msg, target, reason):
    em = nextcord.Embed(description=msg.content, timestamp=msg.created_at)
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
    async def cmd_jailaflemmedetoutbanalamain(self, *args, message : nextcord.Message, client, **_):
        channel = client.get_channel(int(args[0]))
        start_msg_id = int(args[1])
        end_msg_id = int(args[2])
        log_channel = client.get_channel(int(args[3]))

        print("loading history")
        history : List[nextcord.Message] = await channel.history(after=channel.get_partial_message(start_msg_id),
                                        before=channel.get_partial_message(end_msg_id),
                                        limit=None).flatten()
        print(f"Found {len(history)} messages")
        for msg in history:
            print(msg.type)
            if msg.type == nextcord.MessageType.new_member:
                print(msg.author, len(msg.author.roles))
                if len(msg.author.roles) != 1:
                    await channel.send(f"Error while banning {msg.author.mention}, this member not have only 1 role")
                    continue
                try:
                    await msg.author.send(SCAM_BOT)
                    await msg.author.ban(reason="Scam Bot")
                    await log_channel.send(f"<@{msg.author.id}> a été banni pour SCAM")
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
