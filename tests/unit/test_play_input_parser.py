#!usr/bin/env python3
import pytest

import tests.constants
from pipo_hub.cogs.music_bot import InputParser
from pipo_hub.config import settings


@pytest.mark.unit
class TestPlayInputParser:
    @pytest.fixture(scope="function", autouse=True)
    def parser(self):
        return InputParser()

    @pytest.mark.parametrize(
        "input, expected",
        [
            (f"{tests.constants.DUMMY_0}", False),
            (f"{settings.commands.shuffle} {tests.constants.DUMMY_0}", True),
            (
                f"{settings.commands.shuffle} {settings.commands.shuffle} {tests.constants.DUMMY_0}",
                True,
            ),
        ],
    )
    def test_shuffle(self, parser: InputParser, input, expected):
        args = parser.parse_play(input.split())
        assert args.shuffle == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            (f"{tests.constants.DUMMY_0}", False),
            (f"{settings.commands.search} {tests.constants.DUMMY_0}", True),
            (
                f"{settings.commands.search} {settings.commands.search} {tests.constants.DUMMY_0}",
                True,
            ),
        ],
    )
    def test_search(self, parser: InputParser, input, expected):
        args = parser.parse_play(input.split())
        assert args.search == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            (f"{tests.constants.DUMMY_0}", [tests.constants.DUMMY_0]),
            (
                f"{tests.constants.DUMMY_1} {tests.constants.DUMMY_2}",
                [tests.constants.DUMMY_1, tests.constants.DUMMY_2],
            ),
            (
                f"{settings.commands.shuffle} {settings.commands.search} {tests.constants.DUMMY_0}",
                [tests.constants.DUMMY_0],
            ),
        ],
    )
    def test_query(self, parser: InputParser, input, expected):
        args = parser.parse_play(input.split())
        assert args.query == expected

    def test_empty_input(self, parser: InputParser):
        args = parser.parse_play("")
        assert not args.shuffle
        assert not args.search
        assert not args.query
