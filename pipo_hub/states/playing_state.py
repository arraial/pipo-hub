from typing import List

from discord.ext.commands import Context as Dctx

import pipo_hub.states.disconnected_state
import pipo_hub.states.idle_state
import pipo_hub.states.state


class PlayingState(pipo_hub.states.state.State):
    """Bot playing state.

    Bot state while playing music in a voice channel.
    Can process commands:
        * :meth:`leave`
        * :meth:`play`
        * :meth:`skip`
        * :meth:`pause`
    """

    def __init__(self):
        super().__init__("playing")

    async def join(self, ctx: Dctx) -> None:  # noqa: D102
        pass

    async def resume(self) -> None:  # noqa: D102
        pass

    async def clear(self) -> None:
        """Reset music queue and halt currently playing audio.

        Music is stopped and bot transition to Idle State.
        """
        await self.context.player.clear()
        self.context.transition_to(pipo_hub.states.idle_state.IdleState())

    async def pause(self) -> None:
        """Pause currently playing music.

        Pause currently playing music and transition to Idle State.
        """
        self.context.player.pause()
        self.context.transition_to(pipo_hub.states.idle_state.IdleState())

    async def leave(self) -> None:
        """Make bot leave the current server.

        Bot leaves server and transition to Disconnected State.
        """
        await self.context.player.leave()
        self.context.transition_to(
            pipo_hub.states.disconnected_state.DisconnectedState()
        )

    async def play(self, ctx: Dctx, query: List[str], shuffle: bool) -> None:
        """Add music to play.

        Parameters
        ----------
        ctx : Dctx
            Bot context.
        query : List[str]
            Music to play.
        shuffle : bool, optional
            Randomize play order when multiple musics are provided.
        """
        await self.context.player.play(query, shuffle)

    async def skip(self) -> None:
        """Skip currently playing music.

        Skips currently playing music by stopping the voice client, currently playing
        the music.
        """
        self.context.player.skip()
