#!usr/bin/env python3
import mock
import pytest

from pipo_hub.states.idle_state import IdleState
from pipo_hub.states.playing_state import PlayingState
from pipo_hub.states.disconnected_state import DisconnectedState


@pytest.mark.unit
class TestPlayingState:
    __state_name = "playing"

    @pytest.fixture(scope="function")
    def initial_state(self, mocker) -> PlayingState:
        mocker.patch(
            "pipo_hub.states.playing_state.PlayingState.context", new=mock.AsyncMock()
        )
        return PlayingState()

    @pytest.mark.asyncio
    async def test_disabled_commands(self, initial_state: PlayingState):
        initial_state.name == self.__state_name
        context = initial_state.context
        await initial_state.join(None)
        await initial_state.resume()
        assert context == initial_state.context

    @pytest.mark.parametrize(
        "method, args, final_state",
        [
            ("pause", (), IdleState),
            ("leave", (), DisconnectedState),
        ],
    )
    @pytest.mark.asyncio
    async def test_state_transition(
        self, initial_state: PlayingState, method, args, final_state
    ):
        initial_state.name == self.__state_name
        await getattr(initial_state, method)(*args)
        assert len(initial_state.context.transition_to.call_args.args) == 1
        result_state = initial_state.context.transition_to.call_args.args[0]
        assert result_state.name == final_state().name

    @pytest.mark.parametrize(
        "method, args",
        [
            ("skip", ()),
            ("play", (None, ["test"], True)),
        ],
    )
    @pytest.mark.asyncio
    async def test_no_state_transition(self, initial_state: PlayingState, method, args):
        initial_state.name == self.__state_name
        context = initial_state.context
        await getattr(initial_state, method)(*args)
        assert context == initial_state.context
