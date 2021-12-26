from typing import Dict
import json
import re
import nextcord
from asyncio import TimeoutError
from os import path
import logging

from . import ConfigurerTypes
from .exc import *

QUERY_SPLIT_REGEX = re.compile(r"[ =]")
INVALID_USAGE = """Usage invalide:
Utilisez la syntaxe ``variable=valeur`` pour configurer les variables simples.
Pour les listes, utilisez les commandes suivante :
__variable__ add __valeur__ : Ajoute la __valeur__ à la liste.
__variable__ remove __valeur__ : Retire la __valeur__ de la liste.
__variable__ clear : Vide la liste.

Pour terminer l'édition, tapez ``OK``, si vous souhaitez quitter sans sauvegarder, tapez ``CANCEL``.
"""

logger = logging.getLogger("Configurer")

class Configurer:
    def __init__(self, pattern):
        logger.info("Creating new configurer")
        self.msg = None  # type: nextcord.Message
        self.status = None
        self.file = None

        self.params = {}
        for k, v in pattern.items():
            if v.startswith("List/"):
                type_name = v.split('/', 1)[1]
                self.params[k] = ConfigurerTypes.List(subtype=getattr(ConfigurerTypes, type_name))
            else:
                self.params[k] = getattr(ConfigurerTypes, v)()

    @classmethod
    async def open_and_listen(cls, file, pattern, channel, user, client, timeout=60):
        self = await cls.open(file, pattern, channel, member=user, client=client)
        return await self.listen_until_confirmation(channel, user, client, timeout=timeout)

    @classmethod
    async def open(cls, file, pattern, channel, member=None, client=None):
        """
        Args:
            file (str): Path to the config file
            pattern (Dict[str, str]): Dict[option_name, option_type]
            channel (nextcord.Channel): Discord Channel when the prompt will open
            member (nextcord.User): Discord User who can edit the configuration
            client (nextcord.Client): Discord Client object
        Returns:
            Configurer: embed who can be edited
        """
        self = cls(pattern)
        self.file = file
        if path.exists(file):
            with open(file) as fd:
                loaded_json = json.load(fd)
            for k, v in loaded_json.items():
                self.params[k].set_from_json(v)
        await self.init_message(channel, member=member, client=client)
        return self

    async def listen_until_confirmation(self, channel, user, client, timeout=60, delete_after=30):
        def check(m):
            return m.author == user and m.channel == channel

        continue_listen = True
        while continue_listen:
            try:
                msg = await client.wait_for('message', check=check, timeout=timeout)  # type: nextcord.Message
            except TimeoutError:
                logger.info("Configurer listener timed out")
                await channel.send("Time out: sauvegarde en cours ...")
                await self.save(channel=channel)
                return False
            try:
                continue_listen = await self.query(msg)
                await self.update_message()
            except ConfigurerException as e:
                logger.info(f"Error {e.__class__.__name__}: {e}")
                await channel.send(f"Error {e.__class__.__name__}: {e}", delete_after=delete_after)
            try:
                await msg.delete()
            except nextcord.HTTPException:
                pass
        logger.info("Exiting Configurer listener")
        return True

    async def query(self, message: nextcord.Message) -> bool:
        logger.info(f"Reading Query from {message.author}: {message.content}")
        content = message.content  # type: str
        if content == "OK":
            self.status = "L'édition est terminée"
            await self.save(channel=message.channel)
            return False
        if content == "CANCEL":
            self.status = "L'édition est terminée (annulée)"
            return False

        split_result = QUERY_SPLIT_REGEX.split(content, 1)
        if len(split_result) != 2:
            raise InvalidCommand(INVALID_USAGE)

        name, value = split_result
        if name not in self.params:
            raise VariableNotFound(f"Variable {name} inconnue.")

        if isinstance(self.params[name], ConfigurerTypes.List):
            args = value.split(' ', 1)
            if args[0] in ["clear"]:
                self.params[name].clear()
            elif len(args) != 2:
                raise MissingValue("Value is required for adding/removing from list")
            elif args[0] in ["add", "append"]:
                self.params[name].add(args[1])
            elif args[0] in ["del", "remove"]:
                self.params[name].remove(args[1])
        else:
            splited = content.split('=', 1)
            if len(splited) == 1:
                raise InvalidCommand("Syntaxe correcte => ``variable = valeur``")
            name, value = [i.strip() for i in content.split('=', 1)]
            if not self.params[name].is_valid(value):
                raise InvalidValue(f"\"{value}\" est incompatible avec le type {self.params[name].__class__.__name__}")
            self.params[name] = type(self.params[name])(value)
        return True

    async def init_message(self, channel, member=None, client=None):
        if client and (not hasattr(channel, "guild") or not channel.guild.get_member(client.user.id).permissions_in(channel).manage_messages):
            await channel.send("AVERTISSEMENT: Le bot n'a pas la permission \"Manage messages\" et ne peux donc pas nettoyer automatiquement les query")
        self.msg = await channel.send(embed=nextcord.Embed(title="Loading ..."))
        await self.update_message(status=f"En édition par: {member.mention}")

    async def update_message(self, status=None):
        if status:
            self.status = status
        em = nextcord.Embed(title="Configuration", description=self.status)
        for k, v in self.params.items():
            display = str(v)
            em.add_field(name=f"{k} ({v.type})", value=display if display else "\u200b", inline=False)
        em.set_footer(text="Tapez ``variable=valeur`` pour changer les configs. une fois fini tapez ``OK``.")
        await self.msg.edit(embed=em)

    async def logging(self, message, *, channel):
        if channel:
            await channel.send(message)

    async def save(self, file=None, channel=None):
        self.raw_save(file)
        await self.logging("La configuration a bien été sauvegardé !", channel=channel)

    def raw_save(self, file=None):
        if file is None:
            file = self.file
        with open(file, 'w') as fd:
            logger.info(f"Saving to {file}")
            json.dump(self.to_json(), fd)

    def to_json(self):
        return {k: v.to_json() for k, v in self.params.items()}