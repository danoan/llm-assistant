from danoan.llm_assistant.core import er

from typing import Any, Dict


class MockEventRunner(er.EventRunner):
    def loop_logic(self, next: er.Event) -> Dict[str, Any]:
        if next.id == "SayHi":
            callback_data = {"name": "John"}
        elif next.id == "SayHello":
            callback_data = {"name": "Alice"}

        if len(self) == 0:
            self.finish()

        return callback_data


def test_event_runner_cycle():
    myer = MockEventRunner()

    hi_name = None

    def sayhi_cb(name: str):
        nonlocal hi_name
        hi_name = name

    hello_name = None

    def sayhello_cb(name: str):
        nonlocal hello_name
        hello_name = name

    sayhi = er.Event("SayHi", None, sayhi_cb)
    sayhello = er.Event("SayHello", None, sayhello_cb)

    myer.push(sayhi)
    myer.push(sayhello)

    assert myer.top() == sayhi
    assert len(myer) == 2

    myer.run()

    assert hi_name == "John"
    assert hello_name == "Alice"
    assert len(myer) == 0

    assert myer.top() is None
    assert myer.pop() is None
