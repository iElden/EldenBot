import gspread
import random
import nextcord
from oauth2client.service_account import ServiceAccountCredentials as sac

class Announce:
    def __init__(self, game, line : list):
        self.game = game
        self.announce = line[0]
        self.color = int(line[1], base=16)
        self.title = line[2] if line[2] else None
        self.texts = [ann for ann in line[3:] if ann]
    async def send(self, author=None, mp=False, image=None,
                   title_args=(), desc_args=None) -> nextcord.Message:
        if desc_args is None:
            desc_args = {}
        channel = author if mp else self.game.channel
        em = nextcord.Embed(title=self.title.format(*title_args), colour=self.color,
                           description=random.choice(self.texts).format(**desc_args))
        if author:
            em.set_author(name=author.name, icon_url=author.avatar_url)
        if image:
            em.set_thumbnail(url=image)
        channel = author if mp else self.game.channel
        return await channel.send(embed=em)


ANN_GDOC_KEY = "1-JJZmP9SPJbzsRHXvBPbFTIDejwN2goqtHPv-Vdqtcg"
GOOGLE_TOKEN_PATH = "private/googlekey.json"

def load_announce(game) -> dict:
    credentials = sac.from_json_keyfile_name(GOOGLE_TOKEN_PATH,
                                             ["https://spreadsheets.google.com/feeds"])
    gc = gspread.authorize(credentials)
    wb = gc.open_by_key(ANN_GDOC_KEY).get_worksheet(0)
    data = wb.get_all_values()[1:]
    result = []
    return {line[0]: Announce(game, line) for line in data if any(line)}


def load_images(game) -> dict:
    credentials = sac.from_json_keyfile_name(GOOGLE_TOKEN_PATH,
                                             ["https://spreadsheets.google.com/feeds"])
    gc = gspread.authorize(credentials)
    wb = gc.open_by_key(ANN_GDOC_KEY).get_worksheet(1)
    data = wb.get_all_values()[1:]
    result = []
    return {line[0]: line[1:] for line in data if any(line)}
