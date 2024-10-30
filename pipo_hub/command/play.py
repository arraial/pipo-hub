from dataclasses import dataclass
from typing import List

from discord.ext.commands import Context as Dctx

from pipo_hub.command.command import Command
from pipo_hub.pipo import Pipo


@dataclass
class Play(Command):
    """Command to play music."""

    bot: Pipo
    ctx: Dctx
    query: List[str]
    shuffle: bool

    async def _execute(self) -> None:
        await self.bot.play(self.ctx, self.query, self.shuffle)
