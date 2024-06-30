import time
from typing import Optional
from enum import Enum
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.console import Console as RichConsole
from danoan.llm_assistant.core import api, exception


from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import deque
from typing import Any, Callable, Deque, Dict


def ensure_environment_variable_is_defined(logger):
    try:
        api.get_configuration_folder()
    except exception.EnvironmentVariableNotDefinedError:
        logger.error(
            f"The environment variable {api.LLM_ASSISTANT_ENV_VARIABLE} is not defined. Please define it before proceeding."
        )
        exit(1)


def ensure_configuration_file_exist(logger):
    ensure_environment_variable_is_defined(logger)
    try:
        api.get_configuration()
    except exception.ConfigurationFileDoesNotExistError:
        logger.error(
            f"The file {api.get_configuration_filepath()} was not found. You can create one by calling llm-assistant setup init"
        )
        exit(1)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def value_or_default(data_dict, key, default: Any):
    if key in data_dict:
        return data_dict[key]
    else:
        return default


# -------------------- EventListener --------------------

# TODO: Make parameters and callback optional


@dataclass
class Event:
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

    def __len__(self):
        return len(self._events)

    @abstractmethod
    def run(self):
        ...


class RichCLIEventRunner(EventRunner):
    class EventName(Enum):
        PrintError = ("PrintError",)
        PrintPanel = ("PrintPanel",)
        PrintList = ("PrintList",)
        PrintPrompt = "Prompt"

    def __init__(self):
        super().__init__()
        self._console = RichConsole()

    def push(self, event: Event):
        if event.id not in self.EventName:
            pass
        return super().push(event)

    def run(self):
        while self._execute:
            time.sleep(0.05)
            if len(self._events) == 0:
                continue

            next = self.top()
            callback_data = None
            if next.id == self.EventName.PrintError:
                message = next.parameters["message"]
                panel = Panel(message, style="red")

                self._console.print(panel)
            elif next.id == self.EventName.PrintPanel:
                message = next.parameters["message"]
                title = value_or_default(next.parameters, "title", None)
                color = value_or_default(next.parameters, "color", "")

                panel = Panel(message, style=color, title=title)
                self._console.print(panel)
            elif next.id == self.EventName.PrintList:
                list_elements = next.parameters["list_elements"]
                numbered = value_or_default(next.parameters, "numbered", True)

                if numbered:
                    list_elements = [
                        f"{i}. {s}" for i, s in enumerate(list_elements, 1)
                    ]

                columns = Columns(list_elements)
                self._console.print(columns)
                self._console.print("")
            elif next.id == self.EventName.PrintPrompt:
                message = next.parameters["message"]

                text = Text(message)
                text.stylize("bold")
                self._console.print(text, end="")

                prompt_value = input("")
                callback_data = {"prompt_value": prompt_value}

            else:
                self.pop()
                continue

            self.pop()
            if next.callback:
                if callback_data is None:
                    callback_data = {}
                next.callback(**callback_data)


@dataclass
class StateOutput:
    next_state: str
    next_state_input: Optional[Dict[str, Any]]


class StateMachine:
    StartState = "start"
    EndState = "end"

    def __init__(self):
        self._nodes = {}
        self._current = self.StartState

    # TODO: Make possible to pass None as input instead of an empty dict
    # Internally I can pass an empty dict
    def set_start_state(self, state: str):
        self._nodes[self.StartState] = lambda: StateOutput(state, {})

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
