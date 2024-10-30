import logging
from abc import ABC, abstractmethod
from typing import List

from discord.ext.commands import Context as Dctx


class Context:
    """State machine context."""

    _state = None
    _logger: logging.Logger

    def __init__(self, state) -> None:
        self._logger = logging.getLogger(__name__)
        self.transition_to(state)

    def transition_to(self, state):
        """Transition state to a new one.

        Parameters
        ----------
        state : State
            Next state to transition.
        """
        self._state = state
        self._state.context = self
        self._logger.info("Current State %s", self._state.name)


class State(ABC):
    """State machine base.

    Declares methods all concrete State should
    implement and provides a reference to the associated Context object,
    which can be used by States to transition Context to another State.
    """

    name: str
    _context: Context
    _logger: logging.Logger

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(__name__)
        self.name = name

    @property
    def context(self) -> Context:
        """Associated context."""
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        """Set context."""
        self._context = context

    @abstractmethod
    async def join(self, ctx: Dctx) -> None:
        """Make bot connect to voice channel."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def skip(self) -> None:
        """Skip currently playing music."""
        pass

    @abstractmethod
    async def leave(self) -> None:
        """Make bot leave the current server."""
        pass

    @abstractmethod
    async def resume(self) -> None:
        """Resume previously paused music."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Reset music queue and halt currently playing audio."""
        pass

    @abstractmethod
    async def pause(self) -> None:
        """Pause currently playing music."""
        pass
