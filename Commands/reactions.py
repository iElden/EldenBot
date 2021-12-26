import nextcord
from util.exception import InvalidArgs, NotFound

class CmdReaction:
    async def cmd_addreaction(self, *args : str, client, channel, message, **_):
        if len(args) < 2:
            raise InvalidArgs("Invalid syntax, ``/addreaction message_id emoji_name``")
        if not args[0].isdigit():
            raise InvalidArgs(f"First argument must be a number, got \"{args[0]}\"")
        msg = await channel.fetch_message(int(args[0]))
        if not msg:
            raise NotFound(f"Message with id \"{args[0]}\" not found")
        emoji = nextcord.utils.get(client.emojis, name=args[1])
        if not emoji:
            raise NotFound(f"Emoji named \"{args[1]}\" not found")
        try:
            await message.delete()
        except:
            pass
        await msg.add_reaction(emoji)