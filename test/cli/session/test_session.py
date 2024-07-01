from danoan.llm_assistant.cli.commands import session


def test_session_state_machine():
    SM = session.SessionStateMachine()
    session.register_state_machine_functions(SM.register)
