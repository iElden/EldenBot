import logging
from .abc import AbcConfig

logger = logging.getLogger("Config")


class MithConfig(AbcConfig):
    PATTERN = {
        "mj": "DiscordUser",
        "players": "List/DiscordUser",
        "non_player_can_use_commands": "Bool"
    }
    FILE = "mithJDR"

    @property
    def mj(self):
        return self["mj"]

    @property
    def players(self):
        return self["players"]

    @property
    def non_player_can_use_commands(self):
        return self["non_player_can_use_commands"]

    def can_use_command(self, member_id):
        return self.non_player_can_use_commands or member_id == self.mj or member_id in self.players

logger.info("Chargement des configs")

class GlobalConfig:
    MithJDR = MithConfig()