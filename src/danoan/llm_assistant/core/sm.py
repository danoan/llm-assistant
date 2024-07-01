from abc import ABC
from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, Optional


class StartStateNotRegisteredError(Exception):
    pass


@dataclass
class StateOutput:
    next_state: str
    next_state_input: Optional[Dict[str, Any]]


class StateMachine(ABC):
    StartState = "start"
    EndState = "end"

    def __init__(self):
        self._nodes = {}
        self._current = self.StartState

    def register(self, state: str, action: Callable[[], StateOutput]):
        self._nodes[state] = action

    def _next(self, input: Optional[Dict[str, Any]] = None) -> StateOutput:
        if input is None:
            dict_input = {}
        else:
            dict_input = input
        state_output = self._nodes[self._current](**dict_input)
        self._current = state_output.next_state
        return state_output

    def run(self):
        if self.StartState not in self._nodes:
            raise StartStateNotRegisteredError()

        state_output = self._next()
        while state_output.next_state != self.EndState:
            state_output = self._next(state_output.next_state_input)
            time.sleep(0.05)
