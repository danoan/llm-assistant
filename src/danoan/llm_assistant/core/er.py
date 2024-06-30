from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
import time
from typing import Any, Callable, Deque, Dict


@dataclass
class Event:
    # TODO: Make parameters and callback optional
    id: str
    parameters: Dict[str, Any]
    callback: Callable[[], Any]


class EventRunner(ABC):
    def __init__(self):
        self._events: Deque = deque()
        self._execute = True

    def push(self, event: Event):
        self._events.append(event)

    def pop(self) -> Event:
        return self._events.popleft()

    def top(self) -> Event:
        return self._events[0]

    def finish(self):
        self._execute = False

    def run(self):
        while self._execute:
            time.sleep(0.05)
            if len(self._events) == 0:
                continue

            next = self.top()
            callback_data = self.loop_logic(next)
            self.pop()

            if next.callback:
                if callback_data is None:
                    callback_data = {}
                next.callback(**callback_data)

    def __len__(self):
        return len(self._events)

    @abstractmethod
    def loop_logic(self, next: Event) -> Dict[str, Any]:
        ...
