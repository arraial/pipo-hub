#!usr/bin/env python3
import mock
import pytest

from pipo_hub.states.idle_state import IdleState
from pipo_hub.states.playing_state import PlayingState
from pipo_hub.states.disconnected_state import DisconnectedState


@pytest.mark.unit
class TestDisconnectedState:
    __state_name = "disconnected"

    @pytest.fixture(scope="function")
    def initial_state(self, mocker) -> DisconnectedState:
        mocker.patch(
            "pipo_hub.states.disconnected_state.DisconnectedState.context",
            new=mock.AsyncMock(),
        )
        return DisconnectedState()

    @pytest.mark.asyncio
    async def test_disabled_commands(self, initial_state: DisconnectedState):
        initial_state.name == self.__state_name
        context = initial_state.context
        await initial_state.skip()
        await initial_state.leave()
        await initial_state.resume()
        await initial_state.clear()
        await initial_state.pause()
        assert context == initial_state.context

    @pytest.mark.parametrize(
        "method, args, final_state",
        [
            ("join", (None,), IdleState),
            ("play", (None, ["test"], True), PlayingState),
        ],
    )
    @pytest.mark.asyncio
    async def test_state_transition(
        self, initial_state: DisconnectedState, method, args, final_state
    ):
        initial_state.name == self.__state_name
        await getattr(initial_state, method)(*args)
        assert len(initial_state.context.transition_to.call_args.args) == 1
        result_state = initial_state.context.transition_to.call_args.args[0]
        assert result_state.name == final_state().name
