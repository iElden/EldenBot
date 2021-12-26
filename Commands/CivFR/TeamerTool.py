import nextcord
from typing import List, Tuple

from util.function import get_member_in_channel

CAP_ID_TO_STYLE = [nextcord.ButtonStyle.gray, nextcord.ButtonStyle.blurple, nextcord.ButtonStyle.red]
TEAM_LETTER = ['O', 'A', 'B']

class PlayerPickerButton(nextcord.ui.Button):
    def __init__(self, name, row, is_captain):

        super().__init__(style=CAP_ID_TO_STYLE[is_captain], label=name, row=row, disabled=bool(is_captain))

    async def callback(self, interaction: nextcord.Interaction):
        view : TeamBuilderView = self.view
        if interaction.user != view.current_captain_turn:
            return
        self.style = CAP_ID_TO_STYLE[view.pick_phase[view.phase_nb]]
        self.disabled = True
        if view.pick_phase[view.phase_nb] == 1:
            view.team1.append(self.label)
        else:
            view.team2.append(self.label)
        await view.next(interaction)



TMP = ["Pierre", "Paul", "Jack", "Maite", "Michel", "Jean-Remy"]

class TeamBuilderView(nextcord.ui.View):
    children : PlayerPickerButton
    def __init__(self, captains : Tuple[nextcord.Member, nextcord.Member], player_list : List[nextcord.Member]):
        super().__init__()

        #tmp
        player_list = [0] * len(TMP)

        self.captains = captains
        self.current_captain_turn = self.captains[0]
        self.player_list = player_list
        nb_picks = len(player_list) // 2
        self.pick_phase = [1, 2] + [2, 1, 1, 2] * ((nb_picks - 1) // 2) + ([] if nb_picks % 2 else [2, 1])
        self.phase_nb = 0
        self.ended = False
        self.team1 = [captains[0].display_name]
        self.team2 = [captains[1].display_name]

        div = len(player_list) // 5 + 1
        for i, pl in enumerate(player_list):
            is_cap = 0
            if pl == self.captains[0]:
                is_cap = 1
            if pl == self.captains[1]:
                is_cap = 2
            # self.add_item(PlayerPickerButton(pl.display_name, i % div, is_cap))
            self.add_item(PlayerPickerButton(TMP[i], i % div, is_cap))

    async def next(self, interaction : nextcord.Interaction):
        self.phase_nb += 1
        if self.phase_nb >= len(self.pick_phase):
            self.ended = True
            self.stop()
        else:
            self.current_captain_turn = self.captains[self.pick_phase[self.phase_nb] - 1]
        await interaction.response.edit_message(embed=self.to_embed(), view=self)

    def _get_phase_tl(self):
        phase = self.pick_phase
        if self.ended:
            return ' '.join(TEAM_LETTER[i] for i in phase)
        else:
            return (' '.join(TEAM_LETTER[i] for i in phase[:self.phase_nb]) + '<' + TEAM_LETTER[phase[self.phase_nb]]
                    + '>' + ' '.join(TEAM_LETTER[i] for i in phase[self.phase_nb+1:]))

    def to_embed(self):
        if self.ended:
            desc = "Les équipes sont faites !"
        else:
            desc = f"{self.current_captain_turn} doit choisir un joueur\n\n```md\n{self._get_phase_tl()}```"
        em = nextcord.Embed(title="Team Builder", description=desc)
        em.add_field(name="Équipe A", value='\n'.join(self.team1))
        em.add_field(name="Équipe B", value='\n'.join(self.team2))
        return em

class CmdTeamerTools:
    async def cmd_teambuilder(self, *args, member, channel, message : nextcord.Message, **kwargs):
        pls = get_member_in_channel(member.voice)
        if member in pls:
            pls.remove(member)
        view = TeamBuilderView((member, member), pls)
        await channel.send(view=view, embed=view.to_embed())