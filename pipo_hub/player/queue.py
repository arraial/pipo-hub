import logging
from abc import ABC, abstractmethod
from typing import Iterable, Optional, Union


class PlayerQueue(ABC):
    """Player queue.

    Handles added music progress tracking.
    """

    _logger: logging.Logger

    def __init__(
        self,
    ) -> None:
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def add(
        self,
        query: Union[str, Iterable[str]],
        shuffle: bool = False,
    ) -> None:
        """Add music query to queue.

        Parameters
        ----------
        query : Union[str, Iterable[str]]
            Music query to add.
        shuffle : bool, optional
            Whether to shuffle music order, by default False.
        """
        pass

    @abstractmethod
    def get(self) -> Optional[str]:
        """Get one music from queue."""
        return None

    @abstractmethod
    def size(self) -> int:
        """Music to be played.

        Sum of enqueued music.

        Returns
        -------
        int
            Queue size.
        """
        return -1

    @abstractmethod
    def clear(self) -> None:
        """Clear queue."""
        pass
