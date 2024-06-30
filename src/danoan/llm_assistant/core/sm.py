from abc import ABC, abstractmethod
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


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

    def _next(self, input: Dict[str, Any]) -> StateOutput:
        state_output = self._nodes[self._current](**input)
        self._current = state_output.next_state
        return state_output

    def run(self):
        if self.StartState not in self._nodes:
            # TODO: throw error
            pass

        state_output = self._next({})
        while state_output.next_state != self.EndState:
            state_output = self._next(state_output.next_state_input)
            time.sleep(0.05)
