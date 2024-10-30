import asyncio
import pytest
from faststream.rabbit import TestRabbitBroker

import tests.constants
from tests.conftest import Helpers

from pipo_hub.config import settings
from pipo_hub.player.music_queue.music_queue import music_queue
from pipo_hub.player.music_queue.models.music_request import MusicRequest
from pipo_hub.player.music_queue._remote_music_queue import broker, server_publisher


@pytest.mark.wip
@pytest.mark.integration
@pytest.mark.remote_queue
@pytest.mark.xdist_group(name="serial")
class TestRemoteMusicQueue:
    @pytest.fixture(scope="function", autouse=True)
    async def queue(self):
        # TODO change to with_real later and add handle.wait_call
        async with TestRabbitBroker(broker, with_real=settings.player.queue.remote):
            yield music_queue
            music_queue.clear()

    @pytest.mark.parametrize(
        "query",
        [
            (tests.constants.YOUTUBE_URL_1),
            (tests.constants.YOUTUBE_URL_SINGLE_ELEMENT_LIST),
            (tests.constants.YOUTUBE_URL_SIMPLE_LIST),
        ],
    )
    @pytest.mark.youtube
    @pytest.mark.asyncio
    async def test_queue_add(self, queue, query):
        expected = MusicRequest(
            uuid=Helpers.generate_uuid(),
            server_id=queue.server_id,
            query=[query] if isinstance(query, str) else query,
        )

        await queue.add(query=query)
        server_publisher.mock.assert_called_once
        actual = MusicRequest(**server_publisher.mock.call_args.args[0])
        assert actual
        assert Helpers.equal_models(expected, actual, ["uuid"])

    @pytest.mark.parametrize(
        "musics, queue_size",
        [
            (tests.constants.MUSIC_EMPTY_LIST, 0),
            (tests.constants.MUSIC_SINGLE_ELEMENT_LIST, 1),
            (tests.constants.MUSIC_SIMPLE_LIST_1, 2),
        ],
    )
    @pytest.mark.query
    @pytest.mark.asyncio
    async def test_individual_add(self, queue, musics, queue_size):
        [await queue.add(music) for music in musics]
        await asyncio.sleep(tests.constants.TIME_TO_FETCH_MUSIC)
        assert queue.size() == queue_size

    @pytest.mark.parametrize(
        "musics, queue_size",
        [
            (tests.constants.MUSIC_EMPTY_LIST, 0),
            (tests.constants.MUSIC_SINGLE_ELEMENT_LIST, 1),
            (tests.constants.MUSIC_SIMPLE_LIST_1, 2),
        ],
    )
    @pytest.mark.query
    @pytest.mark.asyncio
    async def test_multiple_add(self, queue, musics, queue_size):
        await queue.add(musics)
        await asyncio.sleep(tests.constants.TIME_TO_FETCH_MUSIC * len(musics))
        assert queue.size() == queue_size

    @pytest.mark.parametrize(
        "musics",
        [
            tests.constants.MUSIC_SINGLE_ELEMENT_LIST,
            tests.constants.MUSIC_SIMPLE_LIST_1,
        ],
    )
    @pytest.mark.query
    @pytest.mark.asyncio
    async def test_get_after_individual_add(self, queue, musics):
        [await queue.add(music) for music in musics]
        music = await queue.get(tests.constants.TIME_TO_FETCH_MUSIC)
        assert music

    @pytest.mark.parametrize(
        "musics",
        [
            tests.constants.MUSIC_SINGLE_ELEMENT_LIST,
            tests.constants.MUSIC_SIMPLE_LIST_1,
        ],
    )
    @pytest.mark.query
    @pytest.mark.asyncio
    async def test_get_after_multiple_add(self, queue, musics):
        await queue.add(musics)
        music = await queue.get(tests.constants.TIME_TO_FETCH_MUSIC)
        assert music

    @pytest.mark.parametrize(
        "musics",
        [
            tests.constants.MUSIC_SINGLE_ELEMENT_LIST,
            tests.constants.MUSIC_SIMPLE_LIST_2,
        ],
    )
    @pytest.mark.query
    @pytest.mark.asyncio
    async def test_clear(self, queue, musics):
        await queue.add(musics)
        await asyncio.sleep(tests.constants.TIME_TO_FETCH_MUSIC * len(musics))
        assert queue.size() == len(musics)
        queue.clear()
        assert queue.size() == 0
