#!usr/bin/env python3
import argparse
import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional

from discord.ext import commands

from pipo_hub.command import (
    Clear,
    CommandQueue,
    Pause,
    Play,
    Reboot,
    Resume,
    Skip,
    Status,
)
from pipo_hub.config import settings
from pipo_hub.pipo import Pipo


@dataclass
class PlayArguments:
    """Parsed play arguments."""

    shuffle: bool
    search: bool
    query: List[str]


class InputParser:
    """Parses music bot commands."""

    __parser: argparse.ArgumentParser

    def __init__(self) -> None:
        parser = argparse.ArgumentParser(exit_on_error=False)
        parser.add_argument(
            settings.commands.search,
            dest="search",
            action="store_true",
            required=False,
        )
        parser.add_argument(
            settings.commands.shuffle,
            dest="shuffle",
            action="store_true",
            required=False,
        )
        parser.add_argument("query", nargs="*", default=[])
        self.__parser = parser

    def parse_play(self, args: Iterable[str]) -> Optional[PlayArguments]:
        """Parse play music command.

        Parameters
        ----------
        args : Iterable[str]
            List of arguments to parse.

        Returns
        -------
        Optional[PlayArguments]
            Parsed arguments, None in case of error.
        """
        try:
            args = self.__parser.parse_args(args)
        except (argparse.ArgumentError, SystemExit):
            return None
        return PlayArguments(shuffle=args.shuffle, search=args.search, query=args.query)


class MusicBot(commands.Cog):
    """Music related collection of commands.

    Discord music bot to play audio.
    Functionality includes:
    - playing music from youtube video/playlist urls;
    - clear, skip, pause & resume audio.
    """

    _logger: logging.Logger
    __input_parser: InputParser

    def __init__(self, bot, channel_id: str, voice_channel_id: str):
        self._logger = logging.getLogger(__name__)
        self.bot = bot
        self.__input_parser = InputParser()
        self.pipo = Pipo(self.bot)
        self.pipo.channel_id = channel_id
        self.pipo.voice_channel_id = voice_channel_id
        self.command_queue = CommandQueue()

    @commands.command(
        pass_context=True,
        brief="Play music",
        help="Add music by providing a youtube music/playlist url or search query.\n"
        "Use -q <query> to search for the most related and popular music.\n"
        "Use -s <url> to shuffle a playlist.\n"
        "-play [-q] [-s] <query> | <music_url> | <playlist_url>",
    )
    async def play(self, ctx, *query):  # noqa: D102
        self._logger.info("Received discord command play: %s", query)
        args = self.__input_parser.parse_play(query)
        self._logger.info("Processed play command '%s'", args)
        if args and args.query:
            query = args.query
            query = " ".join(query) if args.search else query
            await self.command_queue.add(Play(self.pipo, ctx, query, args.shuffle))

    @commands.command(
        pass_context=True,
        brief="Clear bot state",
        help="Clear queued music, bot state and leave voice channel.",
    )
    async def clear(self, ctx):  # noqa: D102
        self._logger.info("Received discord command clear")
        await self.command_queue.add(Clear(self.pipo, ctx))

    @commands.command(
        pass_context=True,
        brief="Pause music",
        help="Pause currently playing music.",
    )
    async def pause(self, ctx):  # noqa: D102
        self._logger.info("Received discord command pause")
        await self.command_queue.add(Pause(self.pipo, ctx))

    @commands.command(
        pass_context=True,
        brief="Resume music",
        help="Resume playing previously paused music.",
    )
    async def resume(self, ctx):  # noqa: D102
        self._logger.info("Received discord command resume")
        await self.command_queue.add(Resume(self.pipo, ctx))

    @commands.command(
        pass_context=True,
        brief="Skip music",
        help="Skip currently playing music.",
    )
    async def skip(self, ctx):  # noqa: D102
        self._logger.info("Received discord command skip")
        await self.command_queue.add(Skip(self.pipo, ctx))

    @commands.command(
        pass_context=True,
        brief="Bot status",
        help="Bot queue status.",
    )
    async def status(self, ctx):  # noqa: D102
        self._logger.info("Received discord command status")
        await self.command_queue.add(Status(self.pipo, ctx))

    @commands.command(pass_context=True, brief="Restart bot")
    async def reboot(self, ctx):  # noqa: D102
        self._logger.info("Received discord command reboot")
        await self.command_queue.add(Reboot(self.pipo, ctx))
