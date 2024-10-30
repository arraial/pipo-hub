#!usr/bin/env python3
"""Music Player."""

import asyncio
import hashlib
import logging
from typing import List, Union

from pipo_hub.config import settings
from pipo_hub.player.music_queue.music_queue import music_queue
from pipo_hub.player.queue import PlayerQueue


class Player:
    """Manage music and Discord voice channel interactions.

    Acts as facilitator to manage audio information while interacting with Discord.
    Maintains a music queue to which new audio sources are asynchronously added when
    calling :meth:`~Player.play`. A thread is used to stream audio to Discord
    until the music queue is exhausted. Whether such thread is allowed to continue
    consuming the queue is specified using :attr:`~Player.can_play`.

    Attributes
    ----------
    __bot : :class:`~pipo_hub.bot.PipoBot`
        Client Discord bot.
    __logger : logging.Logger
        Class logger.
    __player_thread : asyncio.Task
        Obtains and plays music from :attr:`~Player._music_queue`.
    _music_queue : :class:`~pipo_hub.player.music_queue.music_queue.MusicQueue`
        Stores music to play.
    can_play : asyncio.Event
        Whether new music from queue can be played.
    """

    __bot: None
    __logger: logging.Logger
    __player_thread: asyncio.Task
    _player_queue: PlayerQueue
    can_play: asyncio.Event

    def __init__(self, bot) -> None:
        """Build music player.

        Parameters
        ----------
        bot : :class:`~pipo_hub.bot.PipoBot`
            Client Discord bot.
        """
        self.__logger = logging.getLogger(__name__)
        self.__bot = bot
        self._player_queue = music_queue
        self.__player_thread = None
        self.can_play = asyncio.Event()

    def clear(self) -> None:
        """Reset music queue and halt currently playing audio."""
        self.__logger.info("Clearing Player state...")
        self._player_queue.clear()
        self.__logger.info("Cleared queues")
        if self.__player_thread:
            self.__player_thread.cancel()
        self.__logger.info("Canceled player thread")
        self.__bot.voice_client.stop()
        self.__logger.info("Stopped voice client")
        self.can_play.clear()
        self.__logger.info("Clearing operation completed")

    def skip(self) -> None:
        """Skip currently playing music."""
        self.__bot.voice_client.stop()

    def pause(self) -> None:
        """Pause currently playing music."""
        self.__bot.voice_client.pause()

    def resume(self) -> None:
        """Resume previously paused music."""
        self.__bot.voice_client.resume()

    async def leave(self) -> None:
        """Make bot leave the current server."""
        await self.__bot.voice_client.disconnect()

    def queue_size(self) -> int:
        """Get music queue size."""
        return self._player_queue.size()

    def player_status(self) -> str:
        """Player status description."""
        queue_size = self.queue_size()
        if queue_size >= 0:
            queue_size = (
                f"{queue_size}+"
                if queue_size >= settings.player.messages.long_queue
                else queue_size
            )
            return f"{25 * '='}\n🎵\tQueue size: {queue_size}\t🎵\n{25 * '='}\n"
        else:
            return settings.player.messages.unavailable_status

    async def play(self, queries: Union[str, List[str]], shuffle: bool = False) -> None:
        """Add music to play.

        Enqueues music to be played when player thread is free and broadcasts such
        availability. Music thread is initialized if not yet available.

        Parameters
        ----------
        queries : Union[str, List[str]]
            Single/list of music or playlist urls. If a query string is provided
            the best guess music is played.
        shuffle : bool, optional
            Randomize play order when multiple musics are provided, by default False.
        """
        if (not self.__player_thread) or (
            self.__player_thread
            and (self.__player_thread.done() or self.__player_thread.cancelled())
        ):
            self._start_music_queue()
        if not isinstance(queries, (list, tuple)):  # ensure an Iterable is used
            queries = [
                queries,
            ]
        await self.__add_music(queries, shuffle)

    async def __add_music(self, queries: List[str], shuffle: bool) -> None:
        """Add music to play queue.

        Enqueues music to be played when player thread is free and broadcasts such
        availability. Music thread is initialized if not yet available.

        Parameters
        ----------
        queries : List[str]
            List comprised of music, search query or playlist urls. If a query string is
            found the best guess music is played.
        shuffle : bool
            Randomize order by which queries are added to play queue.
        """
        self.__logger.info("Processing music query: %s", queries)
        await self._player_queue.add(queries, shuffle)

    def _start_music_queue(self) -> None:
        """Initialize music thread.

        Initializes music thread and allows music queue consumption.
        """
        self.can_play.set()
        self.__player_thread = asyncio.create_task(
            self.__play_music_queue(), name=settings.player.task_name
        )

    async def _submit_music(self, url: str) -> None:
        # TODO consider raised exceptions
        await self.__bot.submit_music(url)

    async def __play_music_queue(self) -> None:
        """Play music task.

        Obtains a music from :attr:`~pipo_hub.play.player.Player._music_queue` and creates
        a task to submit to the Discord bot to be played.
        """
        self.__logger.info("Entering music play loop")
        while await self.can_play.wait():
            self.can_play.clear()
            self.__logger.debug("Music queue size: %s", self.queue_size())
            url = await self._player_queue.get(settings.player.get_music_timeout)
            if url:
                try:
                    self.__logger.info(
                        "Submitting music %s",
                        hashlib.sha1(url.encode(), usedforsecurity=False).hexdigest(),
                    )
                    await self.__bot.submit_music(url)
                except asyncio.CancelledError:
                    self.__logger.debug(
                        "Cancelled task '%s'", settings.player.task_name
                    )
                    raise
                except Exception:
                    self.__logger.warning("Unable to play music %s", url, exc_info=True)
                    await self.__bot.send_message(settings.player.messages.play_error)
            elif url == None:
                self.__logger.info("Exiting music play loop due to empty queue")
                break
            else:
                self.__logger.warning("Unable to play music with invalid url '%s'", url)
            self.can_play.set()
            self.__logger.debug(
                "Will wait for playing music to complete or exit if queue is empty"
            )
        self.can_play.set()
        self.__logger.info("Exiting play music queue loop")
        self.__bot.become_idle()
