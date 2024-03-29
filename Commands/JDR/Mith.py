import json
import nextcord
import gspread
import re
from random import randint, choice as random_choice
from oauth2client.service_account import ServiceAccountCredentials as sac
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO, BufferedIOBase
from typing import List, Tuple
import enum

from .roll_gif import SUCCES_GIF, FAIL_GIF
from ..roll import roll
from util.exception import InvalidArgs, NotFound, BotError, Forbidden
from util.function import get_member
from util.constant import POUBELLE_ID
from util.decorator import refresh_google_token
from Config import GlobalConfig

credentials = sac.from_json_keyfile_name("private/googlekey.json", ["https://spreadsheets.google.com/feeds"])
gc = gspread.authorize(credentials)

CMD_VERSUS_REGEX = re.compile(r"^\s*(?P<comp_atk>[\w ]*\w)\s*((?P<atk_bonus_sign>[+-])\s*(?P<atk_bonus>\d+))?\s*"
                   r"(\|\s*(?P<comp_def>[\w ]*\w)\s*((?P<def_bonus_sign>[+-])\s*(?P<def_bonus>\d+))?)?\s*\s+(?P<def>[\w<>@]+)\s*(#\s*(?P<roller>\w+))?\s*$")
VERSUS_DEFAULT_GROUPS = ["comp_atk", "atk_bonus_sign", "atk_bonus", "comp_def", "def_bonus_sign", "def_bonus", "def", "roller"]
COMPROLL_DESC = ("{member.mention} fait un jet de {comp_name}.\nIl {result.intro_sentence}\n\n{result.format_results}\n\n" +
                 "Dé final : {old_dice}**{final_dice}** / {comp_score}")

# FILE CONST
with open("private/mith_sheets.json") as fd:
    CHAR_SHEET = json.load(fd)
MJ_ID = 203934874204241921
COMP_XP = {"Crédit": 4}

# SHEET CONST

COMP_NAME_COLUMN = 4
COMP_SCORE_MAIN = 9
COMP_SCORE_XPABLE = 9
class COMP_LEVEL(enum.IntEnum):
    NORMAL = 0
    ADEPTE = 1
    MAITRE = 2
STR_TO_COMP_LEVEL = {"Novice": COMP_LEVEL.NORMAL, "Adepte": COMP_LEVEL.ADEPTE, "Maître": COMP_LEVEL.MAITRE}

# BORDER CONST
SIZE = 128
MIN_Y = 16
MAX_Y = SIZE - 16
MIN_X = SIZE - SIZE // 4
MAX_X = SIZE * 6
BORDER_WIDTH = 8
START_X = MIN_X + BORDER_WIDTH
END_X = MAX_X - BORDER_WIDTH

def user_can_use_command(func):
    async def wrapper(self, *args, member, **kwargs):
        if GlobalConfig.MithJDR.can_use_command(member.id) or kwargs["force"]:
            await func(self, *args, member=member, **kwargs)
        else:
            raise Forbidden("Only player can use these command")
    return wrapper


async def create_image(avatar_url, current_hp, max_hp, injury=False, knock=False):
    """

    Args:
        avatar_url (nextcord.Asset):
        current_hp (int):
        max_hp (int):

    Returns:
        Image
    """
    result = Image.new('RGBA', (SIZE * 6, SIZE), (0, 0, 0, 0))
    raw_data = await avatar_url.read()
    raw_avatar = Image.open(BytesIO(raw_data))
    raw_avatar = raw_avatar.resize((SIZE, SIZE), Image.ANTIALIAS)

    if knock:
        raw_avatar = raw_avatar.convert('1').convert('RGBA')
    bigsize = (raw_avatar.size[0] * 3, raw_avatar.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(raw_avatar.size, Image.ANTIALIAS)
    raw_avatar.putalpha(mask)

    # DRAW HP BAR BORDER

    health_percent = current_hp / max_hp
    if health_percent > 0.5:
        health_color = (0x2e, 0xcc, 0x71, 255) # green
    elif health_percent > 0.2:
        health_color = (0xf1, 0xc4, 0x0f, 255) # gold
    else:
        health_color = (0xe7, 0x4c, 0x3c, 255) # red
    pix = result.load()
    for y in range(MIN_Y, MAX_Y):
        for x in range(MIN_X, MAX_X):
            if x in range(START_X, END_X) and y in range(MIN_Y + BORDER_WIDTH, MAX_Y - BORDER_WIDTH):
                if (x - START_X) / (END_X - START_X) <= health_percent:
                    pix[x, y] = health_color
            else:
                if injury:
                    pix[x, y] = (0x40, 0x00, 0x20, 255)  #  black-red
                else:
                    pix[x, y] = (0, 0, 0, 255)  # black

    result.paste(raw_avatar, (0, 0), raw_avatar)
    r = BytesIO()
    result.save(r, format='PNG')
    r.seek(0)
    return r

def parse_competences(wsh : gspread.Worksheet):
    ll = wsh.get_all_values()  # type: List[List[str]]
    comp = []  # type: List[Tuple[str, int, COMP_LEVEL]]
    for line in range(2, 10):
        comp.append((ll[line][COMP_NAME_COLUMN].strip().lower(), int(ll[line][COMP_SCORE_MAIN]), COMP_LEVEL.NORMAL))
    comp_level = COMP_LEVEL.NORMAL
    line = 13
    while ll[line][COMP_NAME_COLUMN] and ll[line][COMP_SCORE_XPABLE]:
        if not ll[line][COMP_SCORE_XPABLE].isnumeric():
            try:
                comp_level = STR_TO_COMP_LEVEL[ll[line][COMP_SCORE_XPABLE]]
            except KeyError:
                raise BotError(
                    f"Unexcepted value when parsing comp score, got \"{ll[line][COMP_SCORE_XPABLE]}\" at line {line} ({ll[line][COMP_NAME_COLUMN]})")
        else:
            comp.append((ll[line][COMP_NAME_COLUMN].strip().lower(), int(ll[line][COMP_SCORE_XPABLE]), comp_level))
        line += 1
    return comp

def xp_roll(line : List[str]) -> dict:
    comp_name = line[4]
    xp = int(line[8]) if line[8] else 0
    total = int(line[9]) if line[9] else 0
    gain_value = COMP_XP.get(comp_name, 6)
    dice = randint(1, 100)
    success = dice > total
    crits = dice > 100 - (5 - total // 20)
    xp_won = (randint(1, gain_value) if success else 0) + (gain_value if crits else 0)
    return {"success": success, "crits": crits, "old_xp": xp, "new_xp": xp + xp_won, "xp_won": xp_won,
            "old_total": total, "new_total": min(total + xp_won, 100), "comp_name": comp_name, "roll": dice}

async def roll_by_comp(comp, name, bonus):
    """
    Args:
        comp (List[Tuple[str, int, COMP_LEVEL]]): comp sheet Tuple[comp_name, score]
        name (str): comp name the player want roll
        bonus (int): bonus/malus dice
        member (nextcord.Member): nextcord member
        message (nextcord.Message): nextcord message
        channel (nextcord.Channel): nextcord channel
    Returns: None
    """
    possibilities = [i for i in comp if i[0].startswith(name)]
    if not possibilities:
        raise NotFound(f"Compétence \"{name}\"non trouvée dans la fiche de personnage")
    if len(possibilities) > 1:
        raise NotFound(f"Plusieurs compétence porte un nom similaire, conflit entre : {', '.join([i[0] for i in possibilities])}")
    comp_name, comp_score, comp_level = possibilities[0]

    total_bonus = bonus + (comp_level == COMP_LEVEL.MAITRE)
    r = roll(f"{1+ abs(total_bonus)}d100")
    rr = sum(r.results, [])
    old_dice = ""
    if len(rr) == 1:
        final_dice = r.total
    else:
        final_dice = (min if total_bonus > 0 else max)(rr)
    if comp_level >= COMP_LEVEL.ADEPTE:
        old_dice = f"~~{final_dice}~~ "
        final_dice -= 10
    verdict = get_final_result(final_dice, comp_score)
    return {"result": r, "old_dice": old_dice, "final_dice": final_dice, "comp_name": comp_name, "comp_level": comp_level,
            "comp_score": comp_score, "verdict": verdict}

def get_final_result(final_dice: int, score: int) -> str:
    if final_dice <= score // 5:
        return "+ Réussite Critique"
    if final_dice <= score // 2:
        return "+ Réussite majeure"
    if final_dice <= score:
        return "+ Réussite"
    if final_dice > 80 + score // 5:
        return "- Echec Critique"
    return "- Echec"


class CmdJdrMith:
    @user_can_use_command
    @refresh_google_token(credentials, gc)
    async def cmd_takedamage(self, *args : List[str], message, member, channel, guild, client, heal=False, **_):
        """
        Args:
            *args (str):
            member (nextcord.Member):
            channel (nextcord.Channel):
            guild (nextcord.Guild):
            client (nextcord.Client):
            **_:

        Returns:

        """
        if len(args) < 1:
            raise InvalidArgs("Usage: /takedamage [joueur] {domage}")
        if len(args) == 1:
            target = member
        else:
            membername = ' '.join(args[:-(len(args) - 1)])
            target = get_member(guild, membername) # type: nextcord.Member
            if not target:
                raise NotFound(f"Member named {membername} not found")
        expr = args[-1]
        roll_result = roll(expr)

        damage = roll_result.total
        if damage < 0:
            damage = 0

        elif heal:
            damage = -damage

        wsh = gc.open_by_key(CHAR_SHEET[str(target.id)]).sheet1
        cell_list = wsh.range('P3:P6')
        old_hp = int(cell_list[0].value)
        new_hp = old_hp - damage
        if new_hp > int(cell_list[1].value):
            new_hp = int(cell_list[1].value)
        if old_hp > 0 and new_hp < 0:
            new_hp = 0
        knock = cell_list[2].value == 'TRUE'
        injury = cell_list[3].value == 'TRUE'

        em = nextcord.Embed(colour=target.colour)
        if roll_result.dices:
            em.add_field(name="Lancé de dé", value=f"{member.mention} {roll_result.intro_sentence}\n{roll_result.format_results}")
        if damage > 0:
            em.add_field(name="Resultat", value=f"{target.mention} a pris **{damage}** point{'s' if damage > 1 else ''} de dégats.\n"
                         f"Il lui reste **{new_hp}** / {cell_list[1].value}", inline=False)
        else:
                em.add_field(name="Resultat", value=f"{target.mention} a gagné **{-damage}** point{'s' if damage > 1 else ''} de vie.\n"
                f"Il lui reste **{new_hp}** / {cell_list[1].value}", inline=False)
        em.set_author(name=target.name, icon_url=target.avatar_url)
        em.set_footer(text=message.content)
        msg = await channel.send(embed=em)

        img = await create_image(target.avatar_url_as(format="png", size=1024), new_hp, int(cell_list[1].value), injury, knock)

        trash_msg = await client.get_channel(POUBELLE_ID).send(file=nextcord.File(fp=img, filename="a.png")) #type: nextcord.Message
        em.set_image(url=trash_msg.attachments[0].url)
        await msg.edit(embed=em)

        cell_list[0].value = new_hp
        wsh.update_cell(3, 12, new_hp)

    @user_can_use_command
    async def cmd_gmroll(self, *args, message, member, client,**_):
        if not args or not args[0]:
            args = "1d100"
        expr = "".join(args)
        r = roll(expr)
        em = nextcord.Embed(
            title="Lancé de dés",
            description=f"{member.mention} {r.intro_sentence}\n\n{r.format_results}\n\nTotal : **{r.total}**",
            colour=member.colour
        ).set_footer(text=message.content).set_author(name=member.name, icon_url=member.avatar_url)
        await message.channel.send(embed=em)
        await client.get_user(203934874204241921).send(embed=em)
        try:
            await message.delete()
        except nextcord.HTTPException:
            pass

    @user_can_use_command
    @refresh_google_token(credentials, gc)
    async def cmd_mithroll(self, *args, message, channel, member, guild, content, **_):
        if '#' in content:
            content, target_query = content.split('#', 1)
            target = get_member(guild, target_query.strip())
        else:
            target = member
        if not args:
            raise InvalidArgs("Usage: /mithroll {comp_name} [+/-][nombre]")
        try:
            wsh = gc.open_by_key(CHAR_SHEET[str(target.id)]).sheet1
        except:
            raise BotError("Impossible d'ouvrir la fiche de personnage du membre")
        comp = parse_competences(wsh)
        re_result = re.search(r".*([+-])\s*(\d+)\s*$", content)
        if re_result:
            sign_char = re_result.group(1)
            name = content.split(sign_char, 1)[0]
            bonus = int(sign_char + re_result.group(2))
        else:
            name, bonus = content, 0

        d = await roll_by_comp(comp, name.strip().lower(), bonus)
        em = nextcord.Embed(
            title="Lancé de dés",
            description=COMPROLL_DESC.format(**d, member=member),
            colour=target.colour
        ).set_footer(text=message.content).set_author(name=target.name, icon_url=target.avatar_url)
        em.add_field(name="Résultat", value=f"```diff\n{d['verdict']}```")
        if d['verdict'] == "- Echec Critique":
            em.set_image(url=random_choice(FAIL_GIF))
        elif d['verdict'] == "+ Réussite Critique":
            em.set_image(url=random_choice(SUCCES_GIF))
        await channel.send(embed=em)

    @user_can_use_command
    @refresh_google_token(credentials, gc)
    async def cmd_mithrollversus(self, *args, message, content, member, channel, guild, **_):
        match = CMD_VERSUS_REGEX.match(content)
        if not match:
            raise InvalidArgs(f"The command content must match regular the regular expression\n``{CMD_VERSUS_REGEX.pattern}``")
        d = {k:v for k, v in match.groupdict().items() if v is not None}
        comp_atk = d['comp_atk']
        atk_bonus = int(d.get('atk_bonus_sign', '+') + d.get('atk_bonus', '0'))
        comp_def = d.get('comp_def', comp_atk)
        def_bonus = int(d.get('def_bonus_sign', '+') + d.get('def_bonus', '0'))
        defenser = get_member(guild, d['def'])
        attacker = d.get('roller', None)
        attacker = member if attacker is None else get_member(guild, attacker)
        try:
            wsh1 = gc.open_by_key(CHAR_SHEET[str(attacker.id)]).sheet1
            wsh2 = gc.open_by_key(CHAR_SHEET[str(defenser.id)]).sheet1
        except:
            raise BotError("Impossible d'ouvrir la fiche de personnage du membre")
        datk = await roll_by_comp(parse_competences(wsh1), comp_atk.strip().lower(), atk_bonus)
        ddef = await roll_by_comp(parse_competences(wsh2), comp_def.strip().lower(), def_bonus)

        em = nextcord.Embed(
            title="Lancé de dés",
            description=f"{attacker.mention} **vs** {defenser.mention}",
            colour=attacker.colour
        ).set_footer(text=message.content).set_author(name=attacker.name, icon_url=attacker.avatar_url)
        em.add_field(name="Attaque", value=COMPROLL_DESC.format(**datk, member=attacker), inline=True)
        em.add_field(name="Défense", value=COMPROLL_DESC.format(**ddef, member=defenser), inline=True)
        em.add_field(name="Résultat", value=f"```diff\n{datk['verdict']}```**VS**```diff\n{ddef['verdict']}```", inline=False)
        if datk['verdict'] == "- Echec Critique":
            em.set_image(url=random_choice(FAIL_GIF))
        elif datk['verdict'] == "+ Réussite Critique":
            em.set_image(url=random_choice(SUCCES_GIF))
        await channel.send(embed=em)


    @user_can_use_command
    @refresh_google_token(credentials, gc)
    async def cmd_xproll(self, *args, member, channel, **_):
        target = member
        try:
            wsh = gc.open_by_key(CHAR_SHEET[str(target.id)]).sheet1
        except:
            raise BotError("Impossible d'ouvrir la fiche de personnage du membre")
        ll = wsh.get_all_values()  # type: List[List[str]]
        if len(ll[0]) < 13:
            raise BotError("La fiche de personnage doit au moins avoir une colonne 'M'")

        recap = []
        to_update = {}
        for i, line in enumerate(ll):
            if line[12] == 'TRUE':  # if column M == TRUE
                last_rec = xp_roll(line)
                recap.append(last_rec)
                if last_rec['success']:
                    to_update[i + 1] = last_rec['new_xp']
        if not recap:
            return await channel.send("Vous n'avez aucun jet d'XP à faire ...")
        await channel.send("```diff\n{}```".format('\n'.join(
           [( f"{'+' if d['success'] else '-'} {d['comp_name'][:16]:<16} {d['roll']:^3}/{d['old_total']:>3}"
            + ' | ' + (f"{d['old_total']:^3}->{d['new_total']:^3} (+{d['xp_won']}){' CRITIQUE' if d['crits'] else ''}" if d['success'] else 'Échoué'))
            for d in recap]
        )))
        up = wsh.range(f"I1:I{len(ll)}")
        up = [gspread.Cell(cell.row, cell.col, to_update[cell.row]) for cell in up if cell.row in to_update]
        if up:
            wsh.update_cells(up)
        up = wsh.range(f"M1:M{len(ll)}")
        for cell in up:
            if cell.value == 'FALSE' or cell.value == 'TRUE':
                cell.value = False
        if up:
            wsh.update_cells(up)


    async def cmd_mithcfg(self, *args, channel, member, client, force, **kwargs):
        if member.id != GlobalConfig.MithJDR.mj and not force:
            raise Forbidden("Seulement le MJ peut éditer les configs")
        await GlobalConfig.MithJDR.open_editor(channel, member, client)

    async def cmd_td(self, *args, **kwargs): await self.cmd_takedamage(*args, **kwargs)
    async def cmd_hd(self, *args, **kwargs): await self.cmd_takedamage(*args, **kwargs, heal=True)
    async def cmd_gr(self, *args, **kwargs): await self.cmd_gmroll(*args, **kwargs)
    async def cmd_mr(self, *args, **kwargs): await self.cmd_mithroll(*args, **kwargs)
    async def cmd_mrv(self, *args, **kwargs):await self.cmd_mithrollversus(*args, **kwargs)
