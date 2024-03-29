import nextcord
import asyncio
from enum import IntEnum
from typing import List, Tuple

from constant import emoji
from util.exception import InvalidArgs, Timeout, ALEDException
from util.function import get_member
from .Draft import get_draft

ICONS = ['?', '🚫', chr(0x1f7eb), chr(0x1f7e6)]
class DraftLineState(IntEnum):
    NONE = 0
    BANNED = 1
    PICKED_1 = 2
    PICKED_2 = 3

    @classmethod
    def get_icon(cls, draftLineState, nb) -> str:
        if draftLineState is not cls.NONE:
            return ICONS[draftLineState.value]
        return emoji.NB[nb]

class DraftLine:
    def __init__(self, draft_line):
        self.state = DraftLineState.NONE
        self.line = draft_line

class DynamicDraft:
    class ActionType(IntEnum):
        BAN = 0
        PICK = 1

    def __init__(self, args, drafts_lines, cap1, cap2):
        self.ban_per_team, self.pick_per_team, self.base_timer = self._parse_args(args, len(drafts_lines))
        self.timer = self.base_timer * 2
        self.ban_phase = [1, 2] * self.ban_per_team
        self.pick_phase = [1, 2] + [2, 1, 1, 2] * ((self.pick_per_team - 1) // 2) + ([] if self.pick_per_team % 2 else [2, 1])
        self.caps = (cap1, cap2)  # type: Tuple[nextcord.Member]

        self.phase = self.ActionType.BAN  # type: DynamicDraft.ActionType
        self.phase_nb = -1  # type: int
        self.is_ended = False
        self._next_phase()

        self.drafts = [DraftLine(draft_line) for draft_line in drafts_lines]  # type: List[DraftLine]

    @staticmethod
    def _parse_args(args, draft_len):
        ban_per_team = 0
        if len(args) >= 6:
            if not args[5].isdigit():
                raise InvalidArgs(f"Number of ban per team must be a int, not \"{args[5]}\"")
            ban_per_team = int(args[5])
        pick_per_team = (draft_len - ban_per_team * 2) // 2
        if len(args) >= 5:
            if args[4] != "max":
                if not args[4].isdigit():
                    raise InvalidArgs(f"Number of pick per team must be a int or \"max\", not \"{args[4]}\"")
                pick_per_team = int(args[4])
                if pick_per_team > (draft_len - ban_per_team * 2) // 2:
                    raise InvalidArgs(f"There is not enough draft for this number of ban/pick per team")
        timer = 60
        if len(args) >= 7:
            if not args[6].isdigit():
                raise InvalidArgs(f"Timer must be a int, not \"{args[6]}\"")
            timer = int(args[6])
        return ban_per_team, pick_per_team, timer

    def to_embed(self):
        descs : List[str] = []
        txt = ""
        for i in self._get_draft():
            if len(txt) + len(i) >= 2000:
                descs.append(txt)
                txt = i
            else:
                txt += '\n' + i
        descs.append(txt)

        em = nextcord.Embed(title="Dynamic Draft", description=descs[0])
        if len(descs) > 1:
            em.add_field(name="\u200b", value=descs[1], inline=False)
        if self.is_ended:
            em.add_field(name="Progression",
                         value=f"Draft terminé\n{ICONS[2]} Équipe de {self.caps[0].mention}\n{ICONS[3]} Équipe de {self.caps[1].mention}",
                         inline=False)
        else:
            em.add_field(name="Progression",
                         value=f"```ml\n{self._get_phase()}``````md\n{self._get_phase_tl()}```\n{self._get_action_needed()} **({max(self.timer, 0)}s)**",
                         inline=False)
        return em

    def get_current_phase(self):
        return self.ban_phase if self.phase == self.ActionType.BAN else self.pick_phase

    def _get_draft(self) -> List[str]:
        result = []
        for i, draft in enumerate(self.drafts):
            result.append(f"{DraftLineState.get_icon(draft.state, i)} {draft.line}")
        return result

    def _get_phase(self) -> str:
        if self.phase == self.ActionType.BAN:
            return f"<Ban> pick"
        return f"ban <Pick>"

    def _get_phase_tl(self) -> str:
        phase = self.get_current_phase()
        if not phase:
            return "..."
        return (' '.join(str(i) for i in phase[:self.phase_nb]) + '<' + str(phase[self.phase_nb])
            + '>' + ' '.join(str(i) for i in phase[self.phase_nb+1:]))

    def _get_action_needed(self):
        return f"{ICONS[self.get_team_needed_for_action() + 1]} {self.get_member_needed_for_action().mention} doit choisir une draft à {'ban' if self.phase == self.ActionType.BAN else 'pick'}"

    def get_team_needed_for_action(self) -> int:
        return self.get_current_phase()[self.phase_nb]

    def get_member_needed_for_action(self) -> nextcord.Member:
        return self.caps[self.get_team_needed_for_action() - 1]

    def update(self, n) -> bool:  # return true if finished
        if n is None:  # player timeout
            return self._next_phase()
        if n > len(self.drafts):
            return False
        if self.drafts[n].state != DraftLineState.NONE:
            return False
        team_needed = self.get_team_needed_for_action()
        if self.phase == self.ActionType.BAN:
            self.drafts[n].state = DraftLineState.BANNED
        elif team_needed == 1:
            self.drafts[n].state = DraftLineState.PICKED_1
        elif team_needed == 2:
            self.drafts[n].state = DraftLineState.PICKED_2
        else:
            raise ALEDException(f"DynamicDraft.update() got {n} as n parameter")
        return self._next_phase()

    def _next_phase(self) -> bool:
        self.phase_nb += 1
        if self.phase_nb >= len(self.get_current_phase()):
            if self.phase == self.ActionType.BAN:
                self.phase = self.ActionType.PICK
                self.phase_nb = 0
            else:
                self.is_ended = True
                return True
        return False

    def update_timer(self, n):
        self.timer -= n

    def reset_timer(self):
        self.timer = self.base_timer * ((self.phase_nb <= 1 and self.phase == self.ActionType.BAN) + 1)


class CmdCivFRDDraft:

    async def cmd_ddraft(self, *args : str, channel, client, member, guild, **_):
        """/ddraft {nb} {bans} {leader_per_draft} {pick_per_team} {ban_per_team} {timer}"""
        if not args:
            raise InvalidArgs("Command should take at least two parameter")
        if not args[1].isdigit():
            raise InvalidArgs("2nd Argument must be a integer (exemple: ``/ddraft @iElden 8``)")
        nb = int(args[1])
        drafts_lines = get_draft(nb, *args[2:4], client=client)
        draft = DynamicDraft(args, drafts_lines, member, get_member(guild, args[0]))

        msg = await channel.send(embed=draft.to_embed())
        for i, _ in enumerate(draft.drafts):
            await msg.add_reaction(emoji.NB[i])

        while True:
            try:
                reaction, _ = await client.wait_for('reaction_add', timeout=3, check=lambda reaction, user: user == draft.get_member_needed_for_action() and reaction.message.id == msg.id)
            except asyncio.TimeoutError:
                if draft.timer > -5:
                    draft.update_timer(3)
                    asyncio.create_task(msg.edit(embed=draft.to_embed()))
                else:
                    draft.reset_timer()
                    draft.update(None)
                    await msg.edit(embed=draft.to_embed())
                continue
            try:
                n = emoji.NB.index(str(reaction))
            except:
                continue
            draft.reset_timer()
            rt = draft.update(n)
            await msg.edit(embed=draft.to_embed())
            if rt:
                break
