from dataclasses import dataclass

from discord.ext.commands import Context as Dctx

from pipo_hub.command.command import Command
from pipo_hub.pipo import Pipo


@dataclass
class Pause(Command):
    """Command to pause music."""

    bot: Pipo
    ctx: Dctx

    async def _execute(self) -> None:
        await self.bot.pause(self.ctx)
