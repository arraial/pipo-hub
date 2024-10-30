from typing import List

from discord.ext.commands import Context as Dctx

import pipo_hub.states.idle_state
import pipo_hub.states.playing_state
import pipo_hub.states.state


class DisconnectedState(pipo_hub.states.state.State):
    """Bot disconnected state.

    Bot state while not connected to a voice channel.
    Can process commands:
        * :meth:`join`
        * :meth:`play`
    """

    def __init__(self):
        super().__init__("disconnected")

    async def join(self, ctx: Dctx) -> None:
        """Connect bot to voice channel.

        Connect bot to voice channel and change state to Idle.

        Parameters
        ----------
        ctx : Dctx
            Bot context.
        """
        await self.context.ensure_connection(ctx)
        self.context.transition_to(pipo_hub.states.idle_state.IdleState())

    async def play(self, ctx: Dctx, query: List[str], shuffle: bool) -> None:
        """Connect bot to voice channel and play music.

        Connect bot to voice channel and play a music, changing the state to Playing.
        query : List[str]
            Music to play.
        shuffle : bool, optional
            Randomize play order when multiple musics are provided.
        """
        await self.context.ensure_connection(ctx)
        await self.context.player.play(query, shuffle)
        self.context.transition_to(pipo_hub.states.playing_state.PlayingState())

    async def skip(self) -> None:  # noqa: D102
        pass

    async def leave(self) -> None:  # noqa: D102
        pass

    async def resume(self) -> None:  # noqa: D102
        pass

    async def clear(self) -> None:  # noqa: D102
        pass

    async def pause(self) -> None:  # noqa: D102
        pass
