#!usr/bin/env python3
import asyncio

import mock
import pytest

import tests.constants
from pipo_hub.states.disconnected_state import DisconnectedState
from pipo_hub.states.idle_state import IdleState
from pipo_hub.states.playing_state import PlayingState


@pytest.mark.unit
class TestIdleState:
    __state_name = "idle"

    @pytest.fixture(scope="function")
    async def initial_state(self, mocker) -> IdleState:
        mocker.patch(
            "pipo_hub.states.idle_state.IdleState.context", new=mock.AsyncMock()
        )
        state = IdleState(tests.constants.IDLE_TIMEOUT)
        yield state
        await state._stop_idle_tracker()

    @pytest.fixture(scope="function")
    def state_tracker_disabled(self, mocker) -> IdleState:
        mocker.patch(
            "pipo_hub.states.idle_state.IdleState.context", new=mock.AsyncMock()
        )
        mocker.patch("pipo_hub.states.idle_state.IdleState._start_idle_tracker")
        mocker.patch("pipo_hub.states.idle_state.IdleState._stop_idle_tracker")
        return IdleState(tests.constants.IDLE_TIMEOUT)

    @pytest.mark.asyncio
    async def test_disabled_commands(self, state_tracker_disabled: IdleState):
        await state_tracker_disabled.join(None)
        await state_tracker_disabled.skip()
        await state_tracker_disabled.pause()
        await state_tracker_disabled.clear()

    @pytest.mark.asyncio
    async def test_idle_timeout(self, initial_state: IdleState):
        assert initial_state.name == self.__state_name
        await asyncio.sleep(tests.constants.IDLE_TIMEOUT + 1)
        assert len(initial_state.context.transition_to.call_args.args) == 1
        next_state = initial_state.context.transition_to.call_args.args[0]
        assert next_state.name == DisconnectedState().name

    @pytest.mark.parametrize(
        "method, args, final_state",
        [
            ("play", (None, ["test"], True), PlayingState),
            ("resume", (), PlayingState),
            ("leave", (), DisconnectedState),
        ],
    )
    @pytest.mark.asyncio
    async def test_state_transition(
        self, state_tracker_disabled: IdleState, method, args, final_state
    ):
        state_tracker_disabled.name == self.__state_name
        await getattr(state_tracker_disabled, method)(*args)
        assert len(state_tracker_disabled.context.transition_to.call_args.args) == 1
        result_state = state_tracker_disabled.context.transition_to.call_args.args[0]
        assert result_state.name == final_state().name
