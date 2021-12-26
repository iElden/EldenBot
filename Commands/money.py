from datetime import datetime, timedelta
from random_message import DAILY_CLAIM
import nextcord
import random
import json

class MoneyDict:
    def __init__(self):
        with open("private/coins.save", 'r') as fd:
            self.dic = json.load(fd)

    def _save(self):
        with open("private/coins.save", 'w') as fd:
            fd.write(json.dumps(self.dic))

    def _return_data(self, id):
        id = str(id)
        if id not in self.dic:
            self.dic[id] = {"money": 0, "last_daily": 0}
            self._save()
        return self.dic[id]

    def get(self, member, guild=None):
        if isinstance(member, int):
            return self._return_data(member)
        if isinstance(member, str):
            m = guild.get_member_named(member)
            if not m: return None
            else: return self._return_data(m.id)
        if isinstance(member, nextcord.User) or isinstance(member, nextcord.Member):
            return self._return_data(member.id)

    def get_money(self, *args, **kwargs):
        return self.get(*args, **kwargs)["money"]

    def add_money(self, target, value, **kw):
        d = self.get(target, **kw)
        d["money"] += value
        self._save()
        return d["money"]

    def remove_money(self, target, value, **kw):
        d = self.get(target, **kw)
        if d["money"] < value or value < 0:
            return False
        d["money"] -= value
        self._save()
        return True

    def set_last_daily(self, target, value, **kw):
        d = self.get(target, **kw)
        d["last_daily"] = value
        self._save()



bank = MoneyDict()

class CmdMoney:
    async def cmd_coins(self, *args, **kw):
        await self.cmd_coin(*args, **kw)

    async def cmd_coin(self, *args, member, channel, guild, **_):
        
        you = False if len(args) >= 1 else True
        if not you:
            target = guild.get_member_named(" ".join(args))
            if not member:
                return await channel.send("J'ai pas trouvé la personne que tu cherches")
        else:
            target = member
        value = bank.get_money(target)
        await channel.send("{} avez {} coins sur votre compte".format("Vous avez" if you else f"{target.name} a", value))

    async def cmd_daily(self, *args, member, channel, **__):
        last_daily = bank.get(member)["last_daily"]
        last_dt = datetime.fromtimestamp(last_daily)
        if last_dt + timedelta(hours=22) < datetime.now():
            bank.add_money(member, 100)
            await channel.send(random.choice(DAILY_CLAIM))
            bank.set_last_daily(member, datetime.now().timestamp())
        else:
            timeleft = str((last_dt + timedelta(hours=22)) - datetime.now()).split('.')[0]
            await channel.send("Veuillez patientez {} avant de vouloir toucher votre récompense".format(timeleft))

    async def cmd_pay(self, *args, guild, channel, member, **_):
        if len(args) < 2:
            return await channel.send("USAGE: /pay {valeur} {membre}")
        target = guild.get_member_named(' '.join(args[1:]))
        if not target:
            return await channel.send("J'ai pas trouvé la personne que tu cherches à payer ...")
        if not args[0].isdigit():
            return await channel.send("Désolé, mais ça c'est pas des chiffres ...")
        value = int(args[0])
        if value < 0:
            return await channel.send("T'essairais pas de m'entuber des fois ? non ?")
        if not bank.remove_money(member, value):
            return await channel.send("Désolé, tu peux pas donner plus que tu as, je fais pas les prets moi.")
        bank.add_money(target, value)
        await channel.send("{} a donné {} coins à {}".format(member.mention, value, target.mention))

