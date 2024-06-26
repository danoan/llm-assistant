from danoan.llm_assistant.core import api, model

from rich.console import Console as RichConsole
from rich.columns import Columns
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

import argparse
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import toml
from typing import List, Optional, Tuple


class SessionMode(Enum):
    # Display menu to select a prompt from the repository
    NoPromptSelected = "No Prompt Selected",
    # Display menu with actions: New instance / Select Instance
    PromptSelected = "Prompt Selected",
    # Enter the name of the instance and the template variable values
    NewInstance = "New Instance",
    # Display menu with available instances
    LoadInstance = "Load Instance",
    # Enters in chat mode
    StartInstance = "Start Instance",
    # Asks if it should continue
    ShouldContinue = "Should Continue",
    # End the session
    EndSession = "End Session",


@dataclass
class SessionState:
    mode: SessionMode
    assets_stack: List = deque(maxlen=10)


def _singleton(cls):
    instances_dict = {}

    def inner(*args, **kwargs):
        if cls not in instances_dict:
            instances_dict[cls] = cls(*args, **kwargs)
        return instances_dict[cls]

    return inner


@_singleton
class Console:
    def __init__(self):
        self.console = RichConsole()

    def print_menu_question(self, text: str):
        panel = Panel(text)
        self.console.print(panel)

    def print_list_table_2(self, a_list: List[str], columns: int = 3, numbered: bool = True):
        grid = Table.grid(expand=True)
        for _ in range(columns):
            grid.add_column()

        rows_per_column = len(a_list)//columns + 1

        rows = []
        for i in range(rows_per_column):
            indexes = [i, i+rows_per_column, i+rows_per_column*2]
            row = []
            for index in indexes:
                if index >= len(a_list):
                    continue
                if numbered:
                    row.append(f"{index+1}. {a_list[index]}")
                else:
                    row.append(a_list[index])
            rows.append(row)

        for row in rows:
            grid.add_row(*row)

        self.console.print(grid, end="\n")
        self.console.print("")

    def print_list_table(self, a_list: List[str], numbered: bool = True):
        if numbered:
            a_list = [f"{i}. {s}" for i, s in enumerate(a_list, 1)]

        columns = Columns(a_list)
        self.console.print(columns)
        self.console.print("")

    def print_input_prompt(self, prompt: str):
        text = Text(prompt)
        text.stylize("bold")
        self.console.print(text, end="")

    def print_error(self, error: str):
        panel = Panel(error, style="red")
        self.console.print(panel)

    def print_user_message(self, message: str, title_complement: Optional[str] = None):
        title = "HUMAN"
        if title_complement:
            title = f"HUMAN - {title_complement}"
        panel = Panel(message, style="cyan", title=title)
        self.console.print(panel)

    def print_ai_message(self, message: str, title_complement: Optional[str] = None):
        title = "AI"
        if title_complement:
            title = f"AI - {title_complement}"

        panel = Panel(message, style="orange1", title=title)
        self.console.print(panel)


def my_input(prompt: str):
    Console().print_input_prompt(prompt)
    return input("")


def is_a_prompt_config_file(filepath: Path) -> Tuple[bool, model.PromptConfiguration]:
    try:
        o = toml.load(filepath)
        prompt_config = model.PromptConfiguration(**o)
        return True, prompt_config
    except:
        return False, None


def validate_int(value, floor, ceiling) -> Optional[int]:
    try:
        v = int(value)
        if v >= floor and v <= ceiling:
            return v
        else:
            Console().print_error("Index out of bound")
    except ValueError:
        Console().print_error("Invalid integer value")

    return None


def retry_until_valid_int(message, floor, ceiling) -> int:
    v_str = my_input(message)
    while not (v := validate_int(v_str, floor, ceiling)):
        v_str = my_input(message)

    return v


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def no_prompt_selected(state: SessionState) -> SessionState:
    assert (state.mode == SessionMode.NoPromptSelected)
    config = api.get_configuration()
    prompt_repository = Path(config.prompt_repository)

    list_prompt_config = []
    for prompt_config_filepath in prompt_repository.rglob("*config.toml"):
        _, prompt_config = is_a_prompt_config_file(prompt_config_filepath)
        if prompt_config:
            list_prompt_config.append(prompt_config)

    if len(list_prompt_config) == 0:
        print(f"No prompt available in the repository: {prompt_repository}")
        exit(0)

    Console().print_menu_question("Select prompt")
    Console().print_list_table([e.name for e in list_prompt_config])

    prompt_index = retry_until_valid_int("Prompt index: ", 1, len(list_prompt_config))

    state.mode = SessionMode.PromptSelected
    state.assets_stack.appendleft(list_prompt_config[prompt_index-1])
    return state


def prompt_selected(state: SessionState) -> SessionState:
    Console().print_menu_question("Choose an option")
    Console().print_list_table(["New instance", "Load instance"])

    selected_option = retry_until_valid_int("Option: ", 1, 2)

    if selected_option == 1:
        state.mode = SessionMode.NewInstance
    elif selected_option == 2:
        state.mode = SessionMode.LoadInstance

    return state


def new_instance(state: SessionState) -> SessionState:
    config_folder = api.get_configuration_folder()
    instances_folder = config_folder / "instances" / \
        normalize_name(state.assets_stack[0].name)
    instances_folder.mkdir(parents=True, exist_ok=True)
    instance_filepaths = list(instances_folder.iterdir())
    instance_names = [f.stem for f in instance_filepaths]

    instance_name = my_input("Enter the instance name: ")
    while instance_name in instance_names:
        Console().print_error("This instance name exist already. Choose another one.")
        instance_name = my_input("Enter the instance name: ")

    def get_assignments():
        assignments_str = my_input("Enter variable assignments: ")
        return assignments_str.split("::")

    def validate_assignments(assignments: List[str]):
        for e in assignments:
            try:
                k, v = e.split("=")
            except ValueError:
                return False

            if k is None or v is None:
                return False

        return True

    assignments = get_assignments()
    while not validate_assignments(assignments):
        Console().print_error(
            "Each assignment should be in the format a=b and consecutive assignments should be separated by ::")
        assignments = get_assignments()

    instance_filepath = instances_folder / f"{instance_name}.toml"

    instance = {}
    for e in assignments:
        k, v = e.split("=")
        instance[k] = v

    with open(instance_filepath, "w") as f:
        toml.dump(instance, f)

    state.mode = SessionMode.StartInstance
    state.assets_stack.appendleft(instance)

    return state


def load_instance(state: SessionState) -> SessionState:
    config_folder = api.get_configuration_folder()
    instances_folder = config_folder / "instances" / \
        normalize_name(state.assets_stack[0].name)
    instance_filepaths = list(instances_folder.iterdir())
    instance_names = [f.stem for f in instance_filepaths]

    Console().print_menu_question("Select instance")
    Console().print_list_table(instance_names)

    selected_instance = retry_until_valid_int("Select instance index: ", 1, len(instance_names))
    instance_filepath = instance_filepaths[selected_instance-1]

    instance = {"name": instance_names[selected_instance-1]}
    with open(instance_filepath, "r") as f:
        instance["variables"] = toml.load(f)

    state.mode = SessionMode.StartInstance
    state.assets_stack.appendleft(instance)

    return state


def start_instance(state: SessionState) -> SessionState:
    instance = state.assets_stack[0]
    prompt_config = state.assets_stack[1]

    chat_title = f"{prompt_config.name}::{instance['name']}"
    message = my_input("Enter message: ")
    Console().print_user_message(message, chat_title)

    response = api.custom(prompt_config, message=message, **instance["variables"])
    Console().print_ai_message(response.content, chat_title)

    state.mode = SessionMode.StartInstance
    return state


def execute_state(state: SessionState) -> SessionState:
    if state.mode == SessionMode.NoPromptSelected:
        return no_prompt_selected(state)
    elif state.mode == SessionMode.PromptSelected:
        return prompt_selected(state)
    elif state.mode == SessionMode.NewInstance:
        return new_instance(state)
    elif state.mode == SessionMode.LoadInstance:
        return load_instance(state)
    elif state.mode == SessionMode.StartInstance:
        return start_instance(state)
    # elif state.mode == SessionMode.ShouldContinue:
    #     return should_continue()


def __pre_new_session__(*args, **kwargs):
    api.LLMAssistant().setup(api.get_configuration())
    state = SessionState(SessionMode.NoPromptSelected)

    while state.mode != SessionMode.EndSession:
        state = execute_state(state)


def new_session_parser(subparser_action=None):
    command_name = "new-session"
    description = ""
    help = description.split(".")[0] if description else ""

    if subparser_action:
        parser = subparser_action.add_parser(
            command_name,
            help=help,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    else:
        parser = argparse.ArgumentParser(
            command_name,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    parser.set_defaults(func=__pre_new_session__, subcommand_help=parser.print_help)

    return parser


def extend_parser(subparser_action=None):
    command_name = "session"
    description = ""
    help = description.split(".")[0] if description else ""

    if subparser_action:
        parser = subparser_action.add_parser(
            command_name,
            help=help,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    else:
        parser = argparse.ArgumentParser(
            command_name,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    subparser = parser.add_subparsers()
    new_session_parser(subparser)

    parser.set_defaults(subcommand_help=parser.print_help)

    return parser
