from dataclasses import dataclass

from discord.ext.commands import Context as Dctx

from pipo_hub.command.command import Command
from pipo_hub.pipo import Pipo


@dataclass
class Status(Command):
    """Command bot to present music queue status."""

    bot: Pipo
    ctx: Dctx

    async def _execute(self) -> None:
        await self.bot.status(self.ctx)
