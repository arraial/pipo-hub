#!usr/bin/env python3
import logging

import discord
from discord.ext import commands

from pipo_hub.config import settings


class PipoBot(commands.Bot):
    """Top level Discord bot.

    Discord bot where functionality Cogs are integrated.
    """

    _logger: logging.Logger

    def __init__(self, command_prefix, description):
        self._logger = logging.getLogger(__name__)
        commands.Bot.__init__(
            self,
            command_prefix=command_prefix,
            case_insensitive=True,
            description=description,
            intents=self.get_intents(),
            help_command=commands.DefaultHelpCommand(
                no_category=settings.commands.help.category
            ),
        )

    @staticmethod
    def get_intents() -> discord.Intents:
        """Define required intents for bot.

        Returns
        -------
        discord.Intents
            Intents required for bot to function.
        """
        intents = discord.Intents.default()
        intents.message_content = True
        return intents

    async def on_ready(self):
        """Triggered when bot reaches a stable functionality state."""
        self._logger.info("Bot is ready")
