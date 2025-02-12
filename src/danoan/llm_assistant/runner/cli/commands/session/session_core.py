from copy import deepcopy
from danoan.llm_assistant.common import model
from danoan.llm_assistant.runner.cli import utils as cli_utils
from danoan.llm_assistant.runner.cli.commands.session.cli_drawer import CLIDrawer
from danoan.llm_assistant.runner.cli.commands.session.task_runner import (
    Task,
    TaskInstruction,
)
from danoan.llm_assistant.runner.core import api

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import toml
from typing import Any, Callable, Dict, Optional


#############################################
# Local model
#############################################


class PromptInterruptedError(Exception):
    pass


@dataclass
class PromptConfigurationWithLocation:
    location: Path
    prompt_config: model.PromptConfiguration


#############################################
# Helper functions
#############################################


ValidationFunction = Callable[[Any], bool]
PromptFunction = Callable[[], str]


def _retry_prompt_until_valid_input(
    prompt_fn: PromptFunction,
    validation_fn: ValidationFunction,
) -> str:
    """
    Ask for user prompt until a condition is valid.

    Prompt blocks the execution until the user enter with some
    input. It is possible to take back the control of the execution
    by checking the task instance that originated the prompt execution.

    Args:
        prompt_fun: Function to collect user input.
        validation_fn: Function that validates user input.
    Raises:
        PromptInterruptedError if prompt is interrupted.
        ValueError if entered value has None value.
    """

    entered_value = None

    while not validation_fn(entered_value):
        try:
            entered_value = prompt_fn()
        except PromptInterruptedError as ex:
            raise ex

    if not entered_value:
        raise ValueError()

    return entered_value


def _validate_int(
    value: Optional[str],
    floor: int,
    ceiling: int,
) -> bool:
    """
    Checks if value is an integer and within the range defined by floor and ceiling.

    Args:
        value: String value to check if it represents an integer.
        floor: Lower bound for the integer value.
        ceiling: Upper bound for the integer value.
    Raises:
        ValueError if string value cannot be converted to integer.
        IndexError if value is out of the [floor,ceiling] range.
    """
    if not value:
        return False

    v = int(value)
    if v >= floor and v <= ceiling:
        return True
    else:
        raise IndexError()

    return False


def _retry_prompt_until_valid_int(
    message: str, floor: int, ceiling: int, cliDrawer: CLIDrawer, task: Task
):
    """
    Prompt until a valid integer is entered.

    Args:
        value: String value to check if it represents an integer.
        floor: Lower bound for the integer value.
        ceiling: Upper bound for the integer value.
        cliDrawer: Interface to collect prompt input and print eventual error messages.
        task: Task from which the prompt was requested.
    """

    def validator(value) -> bool:
        try:
            return _validate_int(value, floor, ceiling)
        except IndexError:
            cliDrawer.print_error(message="Index out of bound")
        except ValueError:
            cliDrawer.print_error(message=f"Invalid integer value: `{value}`")

        return False

    def prompt_fn():
        return cliDrawer.prompt(message=message, task=task)

    return _retry_prompt_until_valid_input(prompt_fn, validator)


class TaskName(Enum):
    NoPromptSelected = ("NoPromptSelected",)
    PromptSelected = ("PromptSelected",)
    NewInstance = ("NewInstance",)
    LoadInstance = ("LoadInstance",)
    StartChat = ("StartChat",)
    ContinueChat = ("ContinueChat",)

    def __str__(self):
        return self.value


def register_tasks(
    cliDrawer: CLIDrawer,
    prompt_repository: Path,
    register_function,
):
    """
    Register the session runner tasks.

    NoPromptSelected -> PromptSelected                   -----> StartChat -> ContinueChat
                            |                            |
                            ------> NewInstance -------- |
                            |                            |
                            ------> LoadInstance ------- |
    """

    @register_function(TaskName.NoPromptSelected, first_task=True)
    def _no_prompt_selected(task: Task) -> Optional[TaskInstruction]:
        list_prompt_config = []
        for prompt_config_filepath in prompt_repository.rglob("*config.toml"):
            _, prompt_config = cli_utils.is_a_prompt_config_file(prompt_config_filepath)
            if prompt_config:
                list_prompt_config.append(
                    PromptConfigurationWithLocation(
                        prompt_config_filepath, prompt_config
                    )
                )

        if len(list_prompt_config) == 0:
            cliDrawer.print_error(
                message=f"No prompt available in the repository: {prompt_repository}"
            )
            return TaskInstruction("NoPromptSelected", None)

        cliDrawer.print_panel(message="Select prompt")
        cliDrawer.print_list(
            list_elements=[e.prompt_config.name for e in list_prompt_config]
        )

        try:
            entered_str = _retry_prompt_until_valid_int(
                "Prompt index: ",
                1,
                len(list_prompt_config),
                cliDrawer,
                task,
            )
            prompt_index = int(entered_str)
        except PromptInterruptedError:
            return None

        return TaskInstruction(
            TaskName.PromptSelected,
            {"prompt_config": list_prompt_config[prompt_index - 1]},
        )

    @register_function(TaskName.PromptSelected)
    def _prompt_selected(
        task: Task, prompt_config: PromptConfigurationWithLocation
    ) -> Optional[TaskInstruction]:
        cliDrawer.print_panel(message="Choose an option")
        cliDrawer.print_list(list_elements=["New instance", "Load instance"])

        try:
            entered_str = _retry_prompt_until_valid_int(
                "Option index: ",
                1,
                2,
                cliDrawer,
                task,
            )
            option_index = int(entered_str)
        except PromptInterruptedError:
            return None

        next_state = None
        if option_index == 1:
            next_state = TaskName.NewInstance
        elif option_index == 2:
            next_state = TaskName.LoadInstance
        elif option_index is None:
            next_state = TaskName.PromptSelected
        else:
            return None

        return TaskInstruction(next_state, {"prompt_config": prompt_config})

    @register_function(TaskName.NewInstance)
    def _new_instance(
        task: Task, prompt_config: PromptConfigurationWithLocation
    ) -> Optional[TaskInstruction]:
        instances_folder = (
            prompt_repository / "instances" / prompt_config.location.parent.name
        )
        instances_folder.mkdir(parents=True, exist_ok=True)
        instance_filepaths = list(instances_folder.iterdir())
        list_instance_names = [f.stem for f in instance_filepaths]

        def validate_instance_name(value: str) -> bool:
            if not value:
                return False

            is_valid = value not in list_instance_names
            if not is_valid:
                cliDrawer.print_error(
                    callback=None,
                    message="This instance name exists already. Choose another one.",
                )

            return is_valid

        instance_name = None
        try:
            instance_name = _retry_prompt_until_valid_input(
                lambda: cliDrawer.prompt(
                    message="Enter the instance name: ", task=task
                ),
                validate_instance_name,
            )
        except PromptInterruptedError:
            return None

        instance_input = {}
        for input_variable in api.get_prompt_input_variables(
            prompt_config.prompt_config
        ):
            instance_input_value = None
            try:
                instance_input_value = cliDrawer.prompt(
                    message=f"{input_variable} (empty to skip): ", task=task
                )
            except PromptInterruptedError:
                return None

            print("input;", instance_input_value)
            instance_input_value = instance_input_value.strip()
            if len(instance_input_value) > 0:
                instance_input[input_variable] = instance_input_value

        assignments_str = "::".join(
            [f"{name}={value}" for name, value in instance_input.items()]
        )
        print("HEYHEYHEY--", assignments_str, "--")

        instance_filepath = instances_folder / f"{instance_name}.toml"

        instance: Dict[str, Any] = {"name": instance_name}
        variables: Dict[str, Any] = {}
        for e in assignments_str.split("::"):
            k, v = e.split("=")
            variables[k] = v
        instance["variables"] = variables

        with open(instance_filepath, "w") as f:
            toml.dump(instance, f)

        return TaskInstruction(
            TaskName.StartChat,
            {"prompt_config": prompt_config.prompt_config, "instance": instance},
        )

    @register_function(TaskName.LoadInstance)
    def _load_instance(
        task: Task, prompt_config: PromptConfigurationWithLocation
    ) -> Optional[TaskInstruction]:
        instances_folder = (
            prompt_repository / "instances" / prompt_config.location.parent.name
        )

        if not instances_folder.exists():
            cliDrawer.print_error(message=f"No instance available for this prompt")
            return TaskInstruction(
                TaskName.PromptSelected, {"prompt_config": prompt_config}
            )

        instance_filepaths = list(instances_folder.iterdir())
        instance_names = [f.stem for f in instance_filepaths]

        cliDrawer.print_panel(callback=None, message="Select instance")
        cliDrawer.print_list(callback=None, list_elements=instance_names)

        try:
            entered_str = _retry_prompt_until_valid_int(
                "Select instance index: ",
                1,
                len(instance_names),
                cliDrawer,
                task,
            )
            instance_index = int(entered_str)
        except PromptInterruptedError:
            return None

        instance_filepath = instance_filepaths[instance_index - 1]

        with open(instance_filepath, "r") as f:
            instance = toml.load(f)

        return TaskInstruction(
            TaskName.StartChat,
            {"prompt_config": prompt_config.prompt_config, "instance": instance},
        )

    @register_function(TaskName.StartChat)
    def _start_chat(
        task: Task, prompt_config: model.PromptConfiguration, instance: Dict[str, Any]
    ) -> Optional[TaskInstruction]:
        message = f"Prompt: {prompt_config.name}\nInstance:{instance['name']}"

        cliDrawer.print_panel(
            callback=None, message=message, color="pink3", title="New Chat"
        )

        return TaskInstruction(
            TaskName.ContinueChat,
            {"prompt_config": prompt_config, "instance": instance},
        )

    @register_function(TaskName.ContinueChat)
    def _continue_chat(
        task: Task, prompt_config: model.PromptConfiguration, instance: Dict[str, Any]
    ) -> Optional[TaskInstruction]:
        chat_title = f"{prompt_config.name}::{instance['name']}"

        message_lines = []
        try:
            while True:
                # TODO: Create a variation of prompt that accept message
                # with several lines
                line = cliDrawer.prompt(task=task, message="Enter message: ")
                if line == "$$":
                    break
                message_lines.append(line)
        except PromptInterruptedError:
            return None

        message = "\n".join(message_lines)

        cliDrawer.print_panel(message=message, color="cyan", title=chat_title)

        response = api.custom(prompt_config, message=message, **instance["variables"])
        cliDrawer.print_panel(
            message=response.content, color="orange1", title=chat_title
        )

        return TaskInstruction(
            TaskName.ContinueChat,
            {"prompt_config": prompt_config, "instance": instance},
        )
