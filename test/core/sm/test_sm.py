from danoan.llm_assistant.core import sm

import pytest


def test_sm_cycle():
    st_select_message = "SelectMessage"
    st_read_message = "ReadMessage"

    MESSAGE = "Your travel plan to Greece is ready."

    def welcome() -> sm.StateOutput:
        return sm.StateOutput(st_select_message, None)

    def select_message() -> sm.StateOutput:
        return sm.StateOutput(st_read_message, {"message": MESSAGE})

    def read_message(message: str) -> sm.StateOutput:
        assert message == MESSAGE
        return sm.StateOutput(sm.StateMachine.EndState, None)

    SM = sm.StateMachine()
    SM.register(sm.StateMachine.StartState, welcome)
    SM.register(st_select_message, select_message)
    SM.register(st_read_message, read_message)

    SM.run()


def test_sm_initialization_error():
    SM = sm.StateMachine()
    with pytest.raises(sm.StartStateNotRegisteredError):
        SM.run()
