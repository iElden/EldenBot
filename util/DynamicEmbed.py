import nextcord
from copy import copy
from typing import List, Tuple, Dict, Optional

EMOJI_FIRST_PAGE = '⏪'
EMOJI_PREV_PAGE = '◀'
EMOJI_NEXT_PAGE = '▶'
EMOJI_LAST_PAGE = '⏩'

class DynamicEmbed:

    dynamic_embeds = {} # type: Dict[int, DynamicEmbed]

    def __init__(self, fields, base_embed=None):
        """
        Args:
            fields (List[List[Tuple[str, str]]]):
            base_embed (nextcord.Embed):
        """
        self.fields = fields
        if not base_embed:
            self.base_embed = nextcord.Embed()
        else:
            self.base_embed = base_embed
        self.message = None # type: Optional[nextcord.Message]
        self.page = 1
        self.max_page = len(fields)

    async def edit_page(self, page_number):
        em = copy(self.base_embed)
        self.page = page_number
        for field in self.fields[page_number - 1]:
            em.add_field(name=field[0], value=field[1], inline=False)
        em.set_footer(text=f"Page {self.page}/{self.max_page}")
        return await self.message.edit(embed=em)

    async def next_page(self):
        if self.page != self.max_page:
            return await self.edit_page(self.page + 1)

    async def prev_page(self):
        if self.page != 1:
            return await self.edit_page(self.page - 1)

    async def first_page(self):
        if self.page != 1:
            return await self.edit_page(1)

    async def last_page(self):
        if self.page != self.max_page:
            return await self.edit_page(self.max_page)

    async def send_embed(self, channel):
        """
        Args:
            channel (nextcord.TextChannel): channel to send the embed

        Returns:
            nextcord.Message: the message sended
        """

        self.message = await channel.send(embed=nextcord.Embed(title="chargement"))
        self.dynamic_embeds[self.message.id] = self
        await self.edit_page(1)
        await self.message.add_reaction(EMOJI_FIRST_PAGE)
        await self.message.add_reaction(EMOJI_PREV_PAGE)
        await self.message.add_reaction(EMOJI_NEXT_PAGE)
        await self.message.add_reaction(EMOJI_LAST_PAGE)


async def on_reaction_change(payload : nextcord.RawReactionActionEvent):
    if payload.message_id in DynamicEmbed.dynamic_embeds:
        de = DynamicEmbed.dynamic_embeds[payload.message_id]
        emoji = str(payload.emoji)
        if emoji == EMOJI_FIRST_PAGE:
            await de.first_page()
        elif emoji == EMOJI_PREV_PAGE:
            await de.prev_page()
        elif emoji == EMOJI_NEXT_PAGE:
            await de.next_page()
        elif emoji == EMOJI_LAST_PAGE:
            await de.last_page()