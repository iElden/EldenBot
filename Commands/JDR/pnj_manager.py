import discord
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
from enum import IntEnum
from util.decorator import refresh_google_token

WEBHOOK_NAME = "Elden's Bot PNJ Manager"
MAIN_GDOC_KEY = "1VwcqFHHsUohEp-jPNJ0pz7gS6s8u9ZPk1bsH6Eoqluo"

class SHEET_COL(IntEnum):
    OWNER_ID = 0
    NAME = 1
    GROUP = 2
    IMAGE_URL = 3

logger = logging.getLogger("PNJ Manager")

class GDocDB:
    creds = ServiceAccountCredentials.from_json_keyfile_name("private/googlekey.json", ["https://spreadsheets.google.com/feeds"])
    gc = gspread.authorize(creds)

    def __init__(self):
        self.wb = self.gc.open_by_key(MAIN_GDOC_KEY)

        self.all_sh = None  # type: List[gspread.Spreadsheet]
        self.all_ll = None  # type: Dict[str, List[List[str]]]
        self.refresh()

    def __getitem__(self, item):
        return self.all_ll.get(str(item), None)

    def refresh(self):
        self.all_sh = self.wb.worksheets()
        self.all_ll = {i.title: i.get_all_values() for i in self.all_sh}

gdb = GDocDB()

async def get_webhook(channel : discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == WEBHOOK_NAME:
            return webhook
    logger.info("PNJ Manager not found, creating webhook ...")
    webhook = await channel.create_webhook(name=WEBHOOK_NAME)
    return webhook

async def get_pnj(ll : [list], pnj_name : str) -> list:
    for line in ll:
        if line[SHEET_COL.NAME].lower().strip() == pnj_name.lower().strip():
            return line
    return None

async def pnj_say(message: discord.Message):
    ll = gdb[message.guild.id]
    if ll is None:
        return
    pnj, content = message.content.split('\n', 1)
    pnj = pnj[2:]
    if pnj:
        line = await get_pnj(ll, pnj)
    else:
        line = await get_pnj(ll, "univers")
    if not line:
        await message.channel.send("Le PNJ {} n'a pas été trouvé".format(pnj))
    if line[SHEET_COL.OWNER_ID] != str(message.author.id) and not message.channel.permissions_for(message.author).manage_messages:
        await message.channel.send("Vous n'avez pas la permission d'utiliser ce personnage\n"
                                   "Vous devez être le posseseur du personnage ou avoir la permission \"Gérer les messages\"")
        return
    webhook = await get_webhook(message.channel)
    await webhook.send(content,
                       username="{}{}".format(line[SHEET_COL.NAME], f" ({line[SHEET_COL.GROUP]})" if line[SHEET_COL.GROUP] else ""),
                       avatar_url=line[SHEET_COL.IMAGE_URL])
    await message.delete()

class CmdPNJManager:
    async def cmd_jdrrefreshchar(self, *args, channel, **_):
        gdb.refresh()
        await channel.send("Updated")

    async def pnj_manager_on_message(self, message: discord.Message):
        if message.content.startswith(">>"):
            await pnj_say(message)
