import asyncio
import logging
from abc import ABC, abstractmethod


class Command(ABC):
    """Abstract Command."""

    async def execute(self) -> None:
        """Command execution method.

        Calls subclass defined _execute method, handling task cancellation logic.
        """
        try:
            await self._execute()
        except asyncio.CancelledError:
            logging.getLogger(__name__).info("Cancelling command")
        except Exception:
            logging.getLogger(__name__).exception("Unable to execute command")

    @abstractmethod
    async def _execute(self) -> None:
        """Subclass specific execution method."""
        pass
