#!usr/bin/env python3
import asyncio
import signal
from typing import List

import discord.ext.commands
from discord.ext.commands import Context as Dctx

import pipo_hub
import pipo_hub.player
import pipo_hub.states.disconnected_state
import pipo_hub.states.idle_state
from pipo_hub.config import settings


class Pipo(pipo_hub.states.Context):
    """Music player bot.

    Converts application side logic to Discord requests.
    """

    bot: discord.ext.commands.Bot
    voice_client: discord.VoiceClient
    music_channel: discord.VoiceChannel
    player: pipo_hub.player.Player

    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(pipo_hub.states.disconnected_state.DisconnectedState())
        self.channel_id = None
        self.voice_channel_id = None
        self.bot = bot
        self.voice_client = None
        self.music_channel = None
        self.player = pipo_hub.player.Player(self)

    def current_state(self) -> str:
        """Provide current state name."""
        return self._state.__name__  # noqa

    def become_idle(self) -> None:
        """Transition bot to idle state."""
        self.transition_to(pipo_hub.states.idle_state.IdleState())

    def queue_size(self) -> int:
        """Provide current queue size."""
        return self.player.queue_size()

    async def ensure_connection(self, ctx: Dctx = None) -> None:
        """Ensure a discord channel connection is established.

        If a connection was already established, retries connecting to channel.
        If no connection was established, creates a connection to the same voice
        channel the caller user was in or to a default channel otherwise.

        Parameters
        ----------
        ctx : Dctx, optional
            Discord context from where to obtain user voice channel, by default None.
        """
        if self.voice_client:
            self._logger.info("Reconnecting channel %s", self.voice_client.channel.name)
            channel_id = self.voice_client.channel.id
        elif ctx and ctx.author.voice:
            self._logger.info(
                "User '%s' requested join to channel %s",
                ctx.author.name,
                ctx.author.voice.channel.name,
            )
            channel_id = ctx.author.voice.channel.id
        else:
            self._logger.info("Joining default channel")
            channel_id = self.voice_channel_id
        channel = self.bot.get_channel(channel_id)
        try:
            self.voice_client = await channel.connect(
                timeout=settings.player.idle.timeout,
                reconnect=True,
                self_mute=True,
                self_deaf=True,
            )
            self._logger.info("Successfully joined channel '%s'", channel.name)
        except (asyncio.TimeoutError, discord.ClientException):
            self._logger.exception("Error joining channel")
            raise

    async def send_message(self, message: str) -> None:
        """Send a message to discord channel."""
        if not self.music_channel:
            self.music_channel = self.bot.get_channel(self.channel_id)
        await self.music_channel.send(message)

    async def submit_music(self, url: str) -> None:  # noqa
        """Submit a music to be played on Discord voice channel.

        Submits a music to Discord voice channel and waits until it is over to
        proceed to terminate task. This waiting mechanism makes use o sequential voice
        client state checks and asyncio.sleep invocations.
        Active reconnection is attempted if a music cannot be played due to connection
        issues and discarded in all other cases.

        Parameters
        ----------
        url : str
            URL of music to play.

        Raises
        ------
        asyncio.CancelledError
            Asyncio task was cancelled.
        """
        try:
            self.voice_client.play(
                await discord.FFmpegOpusAudio.from_probe(
                    url, method="fallback", **settings.pipo.ffmpeg_config
                )
            )
            while self.voice_client.is_playing() or self.voice_client.is_paused():  # noqa
                await asyncio.sleep(settings.pipo.check_if_playing_frequency)
        except asyncio.CancelledError:
            self._logger.debug("Cancelling asyncio sleep")
            await asyncio.shield(
                asyncio.wait_for(
                    asyncio.gather(self.voice_client.disconnect()),
                    timeout=settings.pipo.on_exit_disconnect_timeout,
                )
            )
            self._logger.debug("Cancelled asyncio sleep")
            raise
        except discord.ClientException:
            if not self.voice_client.is_connected():
                self._logger.info("Detected connection issues, attempting reconnection")
                await self.ensure_connection()
                await self.submit_music(url)
                return
            else:
                self._logger.warning(
                    "Unable to play music in Discord voice channel", exc_info=True
                )
        finally:
            self.player.can_play.set()
            self._logger.debug("'can_play' flag was set")

    async def join(self, ctx: Dctx):
        """Join a channel defined in discord context."""
        await self._state.join(ctx)

    async def play(self, ctx: Dctx, query: List[str], shuffle: bool):
        """Add music to play.

        Parameters
        ----------
        ctx : Dctx
            Bot context.
        query : List[str]
            Music to play.
        shuffle : bool
            Randomize play order when multiple musics are provided.
        """
        await self._state.play(ctx, query, shuffle)
        await self.move_message(ctx)

    async def pause(self, ctx: Dctx):
        """Pause currently playing music."""
        await self._state.pause()
        await self.move_message(ctx)

    async def resume(self, ctx: Dctx):
        """Resume previously playing music."""
        await self._state.resume()
        await self.move_message(ctx)

    async def clear(self, ctx: Dctx):
        """Clear music queue and bot state."""
        await self._state.clear()
        await self.move_message(ctx)

    async def skip(self, ctx: Dctx):
        """Skip currently playing music."""
        await self._state.skip()
        await self.move_message(ctx)

    async def reboot(self, ctx: Dctx):
        """Reboot bot."""
        await self._state.leave()  # transition to Disconnected state
        self._logger.info("Rebooting")
        signal.raise_signal(signal.SIGUSR1)

    async def status(self, ctx: Dctx):
        """Send current status to discord channel."""
        await self.move_message(ctx)
        await self.send_message(self.player.player_status())

    async def move_message(self, ctx: Dctx):
        """Move discord processed message request to default music channel."""
        msg = ctx.message
        content = msg.content.encode("utf-8", "ignore").decode()
        await msg.delete(delay=settings.pipo.move_message_delay)
        await self.send_message(f"{msg.author.name}: {content}")
