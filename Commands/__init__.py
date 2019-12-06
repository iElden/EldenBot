import sys
import os
import math
import discord
import signal
import subprocess
import logging
from util.decorator import only_owner

logger = logging.getLogger("CommandInitializer")
logger.info("Loading commands")

from .JDR import CmdJdr
from .TFT.CmdTFT import CmdTFT
from .deleteallmessage import CmdDeleteAllMessage
from .help import CmdHelp
from .info import CmdInfos
from .latex import CmdLatex
from .link import CmdLink
from .lol_score import CmdLolScore
from .LoLQuizz import CmdLoLQuizz
from .moderation_tools import CmdModeration
from .money import CmdMoney
from .music import CmdMusic
from .rgapi import CmdRgapi
from .roll import CmdRoll
from .uselesscmd import CmdUseless
from .verif import CmdVerif
from LoupGarou.lg import CmdLg


class Command(CmdRoll, CmdLatex, CmdRgapi, CmdLink, CmdDeleteAllMessage,
              CmdVerif, CmdLolScore, CmdMusic, CmdModeration, CmdLg,
              CmdMoney, CmdInfos, CmdUseless, CmdHelp,
              CmdJdr, CmdLoLQuizz, CmdTFT):
    sleep = False

    @only_owner
    async def cmd_sleep(self, *_, channel, **__):
        self.sleep = not self.sleep
        await channel.send("switch sleep to {}".format(self.sleep))

    @only_owner
    async def cmd_kill(self, *args, **_):
        os.kill(os.getpid(), signal.SIGKILL)

    @only_owner
    async def cmd_bash(self, *args, message, channel, member, guild, client, force, cmd, **_):
        r = subprocess.run(' '.join(args), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True)
        await channel.send(r.stdout or "(Command return code {})".format(r.returncode))

    @only_owner
    async def python(self, *args, message, channel, member, guild, client, force, cmd, asyncrone=False, **_):
        if asyncrone:
            rt = await eval(" ".join(args).strip('`'))
        else:
            rt = eval(" ".join(args).strip('`'))
        await channel.send(rt)

    async def cmd_python(self, *args, **kwargs):
        await self.python(*args, **kwargs, asyncrone=False)

    async def cmd_apython(self, *args, **kwargs):
        await self.python(*args, **kwargs, asyncrone=True)