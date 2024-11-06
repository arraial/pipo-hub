import asyncio
from typing import Dict, Iterable, Optional

import uuid6
import faststream.rabbit
from expiringdict import ExpiringDict
from faststream.rabbit.fastapi import Logger

from pipo_hub.config import settings
from pipo_hub.player.queue import PlayerQueue
from pipo_hub.player.music_queue.models.music import Music
from pipo_hub.player.music_queue.models.music_request import MusicRequest
from pipo_hub.player.music_queue._remote_music_queue import (
    router,
    hub_queue,
    hub_exch,
    server_publisher,
)


class __RemoteMusicQueue(PlayerQueue):
    """Remote music queue.

    Attributes
    ----------
    __broker : faststream.rabbit.RabbitBroker
        Controls connection to remote queues.
    """

    server_id: str
    __playable_music: asyncio.Queue[str]
    __publisher: faststream.rabbit.RabbitPublisher
    __requests: Dict[str, int]

    def __init__(self, server_id: str, queue_size: int) -> None:
        super().__init__()
        self.__requests = ExpiringDict(
            max_len=settings.player.queue.requests.max,
            max_age_seconds=settings.player.queue.requests.timeout,
        )
        self.server_id = server_id
        self.__publisher = server_publisher
        self.__playable_music = asyncio.Queue(queue_size)

    @staticmethod
    def __generate_uuid() -> str:
        return str(uuid6.uuid7())

    async def add(self, query: str | Iterable[str], shuffle: bool = False) -> None:
        query = [query] if isinstance(query, str) else query
        uuid = self.__generate_uuid()
        request = MusicRequest(
            uuid=uuid,
            server_id=self.server_id,
            shuffle=shuffle,
            query=query,
        )
        self.__requests[request.uuid] = 0
        self._logger.info("Adding request: %s", request.uuid)
        await self.__publisher.publish(request)

    async def _add_music(self, request: Music):
        music = str(request.source)
        if request.uuid in self.__requests:
            self._logger.debug("Item obtained from remote music queue: %s", music)
            try:
                self.__requests[request.uuid] = +1
                await asyncio.wait_for(
                    self.__playable_music.put(music),
                    timeout=settings.player.queue.timeout.consume,
                )
                self._logger.debug("Item stored in local music queue: %s", music)
            except asyncio.TimeoutError:
                self._logger.warning(
                    "Item consumption from remote queue timed out: %s", request.uuid
                )
        else:
            self._logger.warning("Item obtained was discarded: %s", music)

    async def get(self, timeout: int = 0) -> Optional[str]:
        timeout = timeout if timeout > 0 else settings.player.queue.timeout.get_op
        try:
            music = await asyncio.wait_for(self.__playable_music.get(), timeout=timeout)
            self._logger.debug("Item obtained from music queue: %s", music)
            return music
        except asyncio.TimeoutError:
            self._logger.debug("Get operation timed out.")
        return None

    def size(self) -> int:
        return self.__playable_music.qsize()

    def clear(self) -> None:
        self.__requests.clear()
        try:
            while not self.__playable_music.empty():
                self.__playable_music.get_nowait()
        except asyncio.QueueEmpty:
            self._logger.warning("There was an error cleaning locally stored music.")
        self._logger.info("Locally stored music cleaned.")


music_queue = __RemoteMusicQueue(
    settings.server_id, settings.player.queue.max_local_music
)


@router.subscriber(
    queue=hub_queue,
    exchange=hub_exch,
    description="Consumes from hub exchange bound hub client exclusive queue",
)
async def consume_music(request: Music, logger: Logger) -> None:
    logger.info("Received request: %s", request.uuid)
    await music_queue._add_music(request)
