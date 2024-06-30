import threading
from danoan.llm_assistant.cli import utils
from danoan.llm_assistant.core import api, model

import argparse
from enum import Enum
from pathlib import Path
import time
import toml
from typing import Any, Dict, List, Optional, Tuple


def is_a_prompt_config_file(
    filepath: Path,
) -> Tuple[bool, model.PromptConfiguration]:
    try:
        o = toml.load(filepath)
        prompt_config = model.PromptConfiguration(**o)
        return True, prompt_config
    except toml.TomlDecodeError as ex:
        raise ex
    except ValueError:
        return False, None


def create_event(event_name: str, callback, **kwargs):
    return utils.Event(event_name, parameters=kwargs, callback=callback)


def wait_events_to_clean(er: utils.EventRunner):
    while len(er) != 0:
        time.sleep(0.05)


def validate_int(er: utils.EventRunner, value, floor, ceiling) -> Optional[int]:
    try:
        v = int(value)
        if v >= floor and v <= ceiling:
            return v
        else:
            er.push(
                create_event(
                    utils.RichCLIEventRunner.EventName.PrintError,
                    callback=None,
                    message="Index out of bound",
                )
            )
    except ValueError:
        er.push(
            create_event(
                utils.RichCLIEventRunner.EventName.PrintError,
                callback=None,
                message="Invalid integer value",
            )
        )

    return None


def retry_prompt_until_valid_int(er: utils.EventRunner, message, floor, ceiling):
    entered_value = None

    def prompt_callback(prompt_value: str):
        nonlocal entered_value
        entered_value = prompt_value

    event = create_event(
        utils.RichCLIEventRunner.EventName.PrintPrompt, prompt_callback, message=message
    )
    er.push(event)
    wait_events_to_clean(er)
    while not (v := validate_int(er, entered_value, floor, ceiling)):
        er.push(event)
        wait_events_to_clean(er)

    return v


def create_session_state_machine(cliER: utils.EventRunner):
    SM = utils.StateMachine()

    class StateName(Enum):
        NoPromptSelected = ("NoPromptSelected",)
        PromptSelected = ("PromptSelected",)
        NewInstance = ("NewInstance",)
        LoadInstance = ("LoadInstance",)
        StartChat = ("StartChat",)
        ContinueChat = "ContinueChat"

        def __str__(self):
            return self.value

    def no_prompt_selected() -> utils.StateOutput:
        config = api.get_configuration()
        prompt_repository = Path(config.prompt_repository)

        list_prompt_config = []
        for prompt_config_filepath in prompt_repository.rglob("*config.toml"):
            _, prompt_config = is_a_prompt_config_file(prompt_config_filepath)
            if prompt_config:
                list_prompt_config.append(prompt_config)

        if len(list_prompt_config) == 0:
            cliER.push(
                create_event(
                    cliER.EventName.PrintError,
                    None,
                    message=f"No prompt available in the repository: {prompt_repository}",
                )
            )
            return utils.StateOutput("NoPromptSelected", None)

        cliER.push(
            create_event(cliER.EventName.PrintPanel, None, message="Select prompt")
        )
        cliER.push(
            create_event(
                cliER.EventName.PrintList,
                None,
                list_elements=[e.name for e in list_prompt_config],
            )
        )

        prompt_index = retry_prompt_until_valid_int(
            cliER, "Prompt index: ", 1, len(list_prompt_config)
        )

        return utils.StateOutput(
            StateName.PromptSelected,
            {"prompt_config": list_prompt_config[prompt_index - 1]},
        )

    SM.register(StateName.NoPromptSelected, no_prompt_selected)

    def prompt_selected(prompt_config: model.PromptConfiguration) -> utils.StateOutput:
        cliER.push(
            create_event(cliER.EventName.PrintPanel, None, message="Choose an option")
        )
        cliER.push(
            create_event(
                cliER.EventName.PrintList,
                None,
                list_elements=["New instance", "Load instance"],
            )
        )

        option_index = retry_prompt_until_valid_int(cliER, "Option index: ", 1, 2)

        next_state = None
        if option_index == 1:
            next_state = StateName.NewInstance
        elif option_index == 2:
            next_state = StateName.LoadInstance

        return utils.StateOutput(next_state, {"prompt_config": prompt_config})

    SM.register(StateName.PromptSelected, prompt_selected)

    def new_instance(prompt_config: model.PromptConfiguration) -> utils.StateOutput:
        config_folder = api.get_configuration_folder()
        instances_folder = (
            config_folder / "instances" / utils.normalize_name(prompt_config.name)
        )
        instances_folder.mkdir(parents=True, exist_ok=True)
        instance_filepaths = list(instances_folder.iterdir())
        instance_names = [f.stem for f in instance_filepaths]

        instance_name = None

        def instance_name_callback(prompt_value: str):
            nonlocal instance_name
            instance_name = prompt_value

        cliER.push(
            create_event(
                cliER.EventName.PrintPrompt,
                callback=instance_name_callback,
                message="Enter the instance name: ",
            )
        )
        wait_events_to_clean(cliER)
        while instance_name in instance_names:
            cliER.push(
                create_event(
                    cliER.EventName.PrintError,
                    callback=None,
                    message="This instance name exist already. Choose another one.",
                )
            )
            cliER.push(
                create_event(
                    cliER.EventName.PrintPrompt,
                    callback=instance_name_callback,
                    message="Enter the instance name: ",
                )
            )
            wait_events_to_clean(cliER)

        assignments_str = None

        def assignments_callback(prompt_value: str):
            nonlocal assignments_str
            assignments_str = prompt_value

        def get_assignments():
            cliER.push(
                create_event(
                    cliER.EventName.PrintPrompt,
                    callback=assignments_callback,
                    message="Enter variable assignment: ",
                )
            )
            wait_events_to_clean(cliER)
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
            cliER.push(
                create_event(
                    cliER.EventName.PrintError,
                    callback=None,
                    message="Each assignment should be in the format a=b and consecutive assignments should be separated by ::",
                )
            )
            assignments = get_assignments()

        instance_filepath = instances_folder / f"{instance_name}.toml"

        instance = {"name": instance_name}
        variables = {}
        for e in assignments:
            k, v = e.split("=")
            variables[k] = v

        with open(instance_filepath, "w") as f:
            toml.dump(variables, f)
        instance["variables"] = variables

        return utils.StateOutput(
            StateName.StartChat, {"prompt_config": prompt_config, "instance": instance}
        )

    SM.register(StateName.NewInstance, new_instance)

    def load_instance(prompt_config: model.PromptConfiguration) -> utils.StateOutput:
        config_folder = api.get_configuration_folder()
        instances_folder = (
            config_folder / "instances" / utils.normalize_name(prompt_config.name)
        )
        instance_filepaths = list(instances_folder.iterdir())
        instance_names = [f.stem for f in instance_filepaths]

        cliER.push(
            create_event(
                cliER.EventName.PrintPanel, callback=None, message="Select instance"
            )
        )
        cliER.push(
            create_event(
                cliER.EventName.PrintList, callback=None, list_elements=instance_names
            )
        )

        instance_index = retry_prompt_until_valid_int(
            cliER, "Select instance index: ", 1, len(instance_names)
        )
        instance_filepath = instance_filepaths[instance_index - 1]

        instance = {"name": instance_names[instance_index - 1]}
        with open(instance_filepath, "r") as f:
            instance["variables"] = toml.load(f)

        return utils.StateOutput(
            StateName.StartChat, {"prompt_config": prompt_config, "instance": instance}
        )

    SM.register(StateName.LoadInstance, load_instance)

    def start_chat(
        prompt_config: model.PromptConfiguration, instance: Dict[str, Any]
    ) -> utils.StateOutput:
        message = f"Prompt: {prompt_config.name}\nInstance:{instance['name']}"

        cliER.push(
            create_event(
                cliER.EventName.PrintPanel,
                callback=None,
                message=message,
                color="pink3",
                title="New Chat",
            )
        )

        return utils.StateOutput(
            StateName.ContinueChat,
            {"prompt_config": prompt_config, "instance": instance},
        )

    SM.register(StateName.StartChat, start_chat)

    def continue_chat(
        prompt_config: model.PromptConfiguration, instance: Dict[str, Any]
    ) -> utils.StateOutput:
        chat_title = f"{prompt_config.name}::{instance['name']}"

        message = None

        def message_callback(prompt_value: str):
            nonlocal message
            message = prompt_value

        cliER.push(
            create_event(
                cliER.EventName.PrintPrompt, callback=message_callback, message="Enter message: "
            )
        )
        wait_events_to_clean(cliER)

        cliER.push(
            create_event(
                cliER.EventName.PrintPanel,
                callback=None,
                message=message,
                color="cyan",
                title=chat_title,
            )
        )

        response = api.custom(prompt_config, message=message, **instance["variables"])
        cliER.push(
            create_event(
                cliER.EventName.PrintPanel,
                callback=None,
                message=response.content,
                color="orange1",
                title=chat_title,
            )
        )

        wait_events_to_clean(cliER)

        return utils.StateOutput(
            StateName.ContinueChat,
            {"prompt_config": prompt_config, "instance": instance},
        )

    SM.register(StateName.ContinueChat, continue_chat)

    def prologue() -> utils.StateOutput:
        wait_events_to_clean(cliER)
        cliER.finish()
        rich_er_thread.join()

        return utils.StateOutput(utils.StateMachine.EndState, {})

    SM.register("Prologue", prologue)

    rich_er_thread = threading.Thread(target=cliER.run)
    rich_er_thread.start()

    SM.set_start_state(StateName.NoPromptSelected)

    return SM


def __pre_new_session__(*args, **kwargs):
    api.LLMAssistant().setup(api.get_configuration())
    RichER = utils.RichCLIEventRunner()
    SM = create_session_state_machine(RichER)
    SM.run()


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
