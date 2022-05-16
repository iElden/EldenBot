import nextcord
from nextcord import ui, ButtonStyle

from Commands.CivFR.Database import db
from Commands.CivFR.Ranked.RankedFunc import update_player_ranks
from Commands.CivFR.constant import RANKED_ADMIN_ROLES, RANKED_ADMIN_USERS
from util.exception import Forbidden

def member_is_authorised(member) -> bool:
    if member.id in RANKED_ADMIN_USERS:
        return True
    try:
        member_roles = [i.id for i in member.roles]
        for i in RANKED_ADMIN_ROLES:
            if i in member_roles:
                return True
    except AttributeError:
        return False
    return False

class ModButton(ui.Button):
    async def callback(self, interaction: nextcord.Interaction):
        if not member_is_authorised(interaction.user):
            await interaction.send("You are not an authorised Administrator", ephemeral=True)
            raise Forbidden("Member is not a ranked Administrator")

class ModSelect(ui.Select):
    async def callback(self, interaction: nextcord.Interaction):
        if not member_is_authorised(interaction.user):
            await interaction.send("You are not an authorised Administrator", ephemeral=True)
            raise Forbidden("Member is not a ranked Administrator")


class ValidButton(ModButton):
    def __init__(self, view):
        super().__init__(label="Valider", style=ButtonStyle.green, row=3, disabled=not view.report.report_status.is_valid)

    async def callback(self, interaction: nextcord.Interaction):
        await super().callback(interaction)
        view = self.view
        if self.view.report.validated:
            return await interaction.send("Error: Match already Validated", ephemeral=True)
        db.valid_s1_match(view.report)
        await update_player_ranks(view.report)
        await view.report.update_embed(client=view.client)

class ScrapButton(ModButton):
    def __init__(self, view):
        super().__init__(label="Scrap", style=ButtonStyle.red, row=4, disabled=False)

    async def callback(self, interaction: nextcord.Interaction):
        await super().callback(interaction)
        view = self.view
        if self.view.report.validated:
            return await interaction.send("Error: Match already Scrapped", ephemeral=True)
        db.scrap_s1_match(view.report)
        await update_player_ranks(view.report)
        await view.report.update_embed(client=view.client)

class DeleteButton(ModButton):
    def __init__(self, view):
        super().__init__(label="Delete", style=ButtonStyle.red, row=4, disabled=False)

    async def callback(self, interaction: nextcord.Interaction):
        await super().callback(interaction)
        view = self.view
        db.delete_s1_match(view.report)
        await view.report.delete(client=view.client)

class EditButton(ModButton):
    def __init__(self):
        super().__init__(label="Assigner la position", style=ButtonStyle.blurple, row=3)

    async def callback(self, interaction: nextcord.Interaction):
        await super().callback(interaction)
        view : RankedView = self.view
        if not view.player_select.values:
            await interaction.send("Error: No player selected", ephemeral=True)
            return
        player_id = int(view.player_select.values[0])
        if not view.position_select.values:
            await interaction.send("Error: No position selected", ephemeral=True)
            return
        if self.view.report.validated:
            return await interaction.send("Error: Match already Validated", ephemeral=True)
        position = int(view.position_select.values[0])
        view.report.set_player_position(player_id, position)
        await view.report.update_embed(view.client)
        db.update_s1_match(view.report)

class ReportQuitButton(ModButton):
    def __init__(self):
        super().__init__(label="Bannir pour Quit", style=ButtonStyle.red, row=3, disabled=True)

class AutoFillButton(ModButton):
    def __init__(self):
        super().__init__(label="AutoFill players", style=ButtonStyle.blurple, row=3)

    async def callback(self, interaction: nextcord.Interaction):
        await super().callback(interaction)
        view: RankedView = self.view
        view.report.fill_unreported_players()
        db.update_s1_match(view.report)
        await view.report.update_embed(client=view.client)

class PlayerSelect(ModSelect):
    def __init__(self, view):
        player_names = [self.get_player_name(view.client.get_user(i), i) for i in view.report.players]
        super().__init__(placeholder="Select a player to Administrate", row=1,
                         options=[nextcord.SelectOption(label=name, value=str(pl))
                                  for pl, name in zip(view.report.players, player_names)])

    @staticmethod
    def get_player_name(user : nextcord.User, discord_id : int):
        if user:
            return user.name
        return f"<{discord_id}>"


class PositionSelect(ModSelect):
    def __init__(self, view):
        super().__init__(placeholder="Select a position to force assign", row=2,
                         options=[nextcord.SelectOption(label=str(i+1), value=str(i+1))
                                  for i, _ in enumerate(view.report.players)])


class RankedView(ui.View):
    def __init__(self, report, parent : nextcord.PartialMessage, client : nextcord.Client):
        super().__init__(timeout=30)
        self.report = report
        self.parent : nextcord.PartialMessage = parent
        self.client : nextcord.Client = client

        self.player_select = PlayerSelect(self)
        self.position_select = PositionSelect(self)
        self.valid_button = ValidButton(self)

        self.add_item(self.valid_button)
        self.add_item(self.player_select)
        self.add_item(self.position_select)
        self.add_item(EditButton())
        self.add_item(ReportQuitButton())
        self.add_item(ScrapButton(self))
        self.add_item(DeleteButton(self))
        self.add_item(AutoFillButton())

    async def on_timeout(self) -> None:
        await self.parent.edit(view=None)
