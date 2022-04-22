import nextcord
from nextcord import ui, ButtonStyle

from Commands.CivFR.Ranked import commands as ranked_commands

class ValidButton(ui.Button):
    def __init__(self):
        super().__init__(label="Valider", style=ButtonStyle.green, row=3)

    async def callback(self, interaction: nextcord.Interaction):
        view = self.view

class EditButton(ui.Button):
    def __init__(self):
        super().__init__(label="Assigner la position", style=ButtonStyle.blurple, row=3)

    async def callback(self, interaction: nextcord.Interaction):
        view : RankedView = self.view

        if not view.player_select.values:
            ...
        player_id = view.player_select.values[0]
        if not view.position_select.values:
            ...
        position = view.player_select.values[0] if view.player_select.values else None
        view.report.set_player_position(player_id, position)

class ReportQuitButton(ui.Button):
    def __init__(self):
        super().__init__(label="Bannir pour Quit", style=ButtonStyle.red, row=3, disabled=True)

class PlayerSelect(ui.Select):
    def __init__(self, view):
        player_names = [self.get_player_name(view.client.get_user(i), i) for i in view.report.players]
        super().__init__(placeholder="Select a player to Administrate", row=1,
                         options=[nextcord.SelectOption(label=name, value=str(pl))
                                  for pl, name in zip(view.report.players, player_names)])

    @staticmethod
    def get_player_name(user : nextcord.User, discord_id : int):
        if user:
            return user.name
        return f"<@{discord_id}>"


class PositionSelect(ui.Select):
    def __init__(self, view):
        super().__init__(placeholder="Select a position to force assign", row=2,
                         options=[nextcord.SelectOption(label=str(i+1), value=str(i+1))
                                  for i, _ in enumerate(view.report.players)])


class RankedView(ui.View):
    def __init__(self, report : ranked_commands.RankedReport, parent : nextcord.PartialMessage, client : nextcord.Client):
        super().__init__(timeout=30)
        self.report : ranked_commands.RankedReport = report
        self.parent : nextcord.PartialMessage = parent
        self.client : nextcord.Client = client

        self.player_select = PlayerSelect(self)
        self.position_select = PositionSelect(self)

        self.add_item(ValidButton())
        self.add_item(self.player_select)
        self.add_item(self.position_select)
        self.add_item(EditButton())
        self.add_item(ReportQuitButton())

    async def on_timeout(self) -> None:
        await self.parent.edit(view=None)
