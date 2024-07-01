from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any, Callable, Deque, Dict, Optional


@dataclass
class Event:
    id: str
    parameters: Optional[Dict[str, Any]] = None
    callback: Optional[Callable[[], Any]] = None


class EventRunner(ABC):
    class RunnerState(Enum):
        Busy = "Busy",
        Listening = "Listening"

    def __init__(self):
        self._events: Deque = deque()
        self._execute = True
        self._state = EventRunner.RunnerState.Listening

    def push(self, event: Event):
        self._events.append(event)

    def pop(self) -> Event:
        if len(self) > 0:
            return self._events.popleft()
        else:
            return None

    def top(self) -> Optional[Event]:
        if len(self) > 0:
            return self._events[0]
        else:
            return None

    def state(self):
        return self._state

    def finish(self):
        self._execute = False

    def run(self):
        while self._execute:
            time.sleep(0.05)
            if len(self._events) == 0:
                continue

            next = self.pop()
            self._state = EventRunner.RunnerState.Busy
            callback_data = self.loop_logic(next)
            self._state = EventRunner.RunnerState.Listening

            if next.callback:
                if callback_data is None:
                    callback_data = {}
                next.callback(**callback_data)

    def __len__(self):
        return len(self._events)

    @abstractmethod
    def loop_logic(self, next: Event) -> Dict[str, Any]:
        ...
