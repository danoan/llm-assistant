from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.prompt.cli import utils as cli_utils

import argparse
from git.remote import RemoteProgress
from typing import Dict


def __git_event_processor__(op_code, cur_count, max_count=None, message=""):
    d = " "
    if not op_code & RemoteProgress.RECEIVING:
        return

    if max_count:
        percent = (cur_count / max_count) * 100
        print(f"{d*4}Progress: {percent:.2f}% - {message}")


def __get_sync_events_processor__():
    params: Dict = {}
    action = None

    def inner(event, name, value):
        nonlocal params
        nonlocal action
        d = " "
        if event == "sync_config":
            if name is None:
                print(
                    "Starting synchronization of local folder with configuration file"
                )
            else:
                print(f"{d*2}{name}: {value}")
        elif event == "fetch":
            print(f"{d*4}Fetching repository: {value}")
        elif event == "checkout":
            print(f"{d*4}Checkout version: {value}")
        elif event == "synced":
            print(f"{d*4}Already synced")
        elif event == "sync_local_folder":
            if name is None:
                print(
                    "Starting synchronization of configuration file with local folder"
                )
            else:
                print(f"{d*2}{name}: {value}")
        elif event == "not_tracked":
            print(f"{d*4}Prompt not tracked. Registering version: {value}")
        elif event == "not_prompt_repository":
            print(f"{d*4}This is not a prompt repository. Skipping it.")
        elif event == "git":
            action = __git_event_processor__
        elif event == "begin":
            params = {}
        elif event == "item":
            params[name] = value
        elif event == "end" and action:
            action(**params)

    return inner


def __sync__(*args, **kwargs):
    """
    Sync prompt repository configuration with local folder.
    """
    config = common.get_configuration()
    api.sync(config.prompt, __get_sync_events_processor__())


def extend_parser(subparser_action=None):
    command_name = "sync"
    description = __sync__.__doc__
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

    parser.set_defaults(func=__sync__, subcommand_help=parser.print_help)

    return parser
