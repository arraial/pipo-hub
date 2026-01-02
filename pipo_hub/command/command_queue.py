import asyncio
import logging
from typing import Set

from opentelemetry import metrics

from pipo_hub.command.command import Command

meter = metrics.get_meter(__name__)
counter = meter.create_counter(
    name="pipo.hub.requests.received",
    description="Number of requests issued to hub",
    unit="requests",
)


class CommandQueue:
    """Queue for asynchronous command execution."""

    _logger: logging.Logger
    __scheduled_tasks: Set[asyncio.Task]

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self.__scheduled_tasks = set()

    async def add(self, command: Command) -> None:
        """Add command to execute.

        Create a task for command to be asynchronously executed.

        Parameters
        ----------
        command : Command
            Command to execute.
        """
        counter.add(1)
        task = asyncio.create_task(
            command.execute(), name=f"command_{command.__class__.__name__}"
        )
        self.__scheduled_tasks.add(task)
        task.add_done_callback(self.__scheduled_tasks.discard)

    def stop(self) -> None:
        """Stop running tasks."""
        for task in self.__scheduled_tasks:
            task.cancel()
