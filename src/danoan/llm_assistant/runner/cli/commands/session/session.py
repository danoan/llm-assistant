from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.runner.cli.commands.session.cli_drawer import CLIDrawer
from danoan.llm_assistant.runner.cli.commands.session.task_runner import (
    TaskRunner,
    TaskInstruction,
    Task,
)

from danoan.llm_assistant.runner.core import api
from danoan.llm_assistant.runner.cli import utils
from danoan.llm_assistant.runner.cli.commands.session import session_core as core

from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Console as RichConsole

from pynput.keyboard import Controller, Key
from pynput import keyboard

import fcntl
import os
from pathlib import Path
import selectors
import sys


def create_non_blocking_input():
    # Set up the selector
    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)

    # Make stdin non-blocking
    fd = sys.stdin.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def input_reader():
        events = sel.select(timeout=0.1)
        for key, mask in events:
            if key.fileobj is sys.stdin:
                try:
                    user_input = sys.stdin.readline().split("\n")[0]
                    return user_input
                except IOError:
                    pass
        return None

    return input_reader


non_blocking_input = create_non_blocking_input()


#############################################
# Rich Command Line
#############################################


class _RichCLIDrawer(CLIDrawer):
    def __init__(self):
        self._console = RichConsole()

    def print_error(self, **kwargs):
        message = kwargs["message"]
        panel = Panel(message, style="red")

        self._console.print(panel)

    def print_panel(self, **kwargs):
        message = kwargs["message"]
        title = utils.value_or_default(kwargs, "title", None)
        color = utils.value_or_default(kwargs, "color", "")

        panel = Panel(message, style=color, title=title)
        self._console.print(panel)

    def print_list(self, **kwargs):
        list_elements = kwargs["list_elements"]
        numbered = utils.value_or_default(kwargs, "numbered", True)

        if numbered:
            list_elements = [f"{i}. {s}" for i, s in enumerate(list_elements, 1)]

        columns = Columns(list_elements)
        self._console.print(columns)
        self._console.print("")

    def prompt(self, **kwargs):
        message = kwargs["message"]
        task = kwargs["task"]

        text = Text(message)
        text.stylize("bold")
        self._console.print(text, end="")

        value = None
        with task.get_event_notifier(Task.Event.Stop) as event_notifier:
            while not event_notifier.is_set() and value is None:
                value = non_blocking_input()

        if value is None:
            keyboard = Controller()
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            _ = non_blocking_input()
            raise core.PromptInterruptedError()
        else:
            # Remove session commands from  input
            value = value.replace(f"\x02", "")  # Ctrl+B
            value = value.replace(f"\x11", "")  # Ctrl+Q

        return value


#############################################
# Keyboard Event Listener
#############################################


class KeyboardListener:
    def __init__(self):
        self._events = {}

    def register(self, key_sequence, callback):
        cur_node = self._events
        for key in key_sequence:
            if key not in cur_node:
                cur_node[key] = {}
            cur_node = cur_node[key]

        cur_node["callback"] = callback

    def _on_press(self):
        cur_node = self._events

        def inner(key):
            nonlocal cur_node

            effective_key = None
            if key in cur_node:
                effective_key = key
            elif isinstance(key, keyboard.KeyCode) and key.char in cur_node:
                effective_key = key.char

            if effective_key:
                cur_node = cur_node[effective_key]
            else:
                cur_node = self._events

            if "callback" in cur_node:
                cur_node["callback"]()
                cur_node = self._events

        return inner

    def start(self):
        listener = keyboard.Listener(on_press=self._on_press())
        listener.start()


#############################################
# Argument Parser
#############################################


def start_session():
    config = common.get_configuration()
    api.LLMAssistant().setup(config)

    if not config.prompt_repository and "path" not in config.prompt_repository:
        print("Pront repository path is not configured. Please use the setup command")
        exit(1)

    prompt_repository = Path(config.prompt_repository["path"])
    if not prompt_repository.exists():
        print("Pront repository does not exist. Please use the setup command")
        exit(1)
    cliDrawer = _RichCLIDrawer()
    tr = TaskRunner()
    core.register_tasks(
        cliDrawer,
        prompt_repository,
        tr.register,
    )

    def restart_runner():
        tr.clear()
        tr.add(TaskInstruction(core.TaskName.NoPromptSelected, None))
        tr.next()

    def exit_runner():
        tr.clear()
        tr.stop()
        tr.next()

    # Create a listener
    KL = KeyboardListener()
    KL.register([Key.ctrl_l, "b"], restart_runner)
    KL.register([Key.ctrl_l, "q"], exit_runner)
    KL.start()

    tr.run()
