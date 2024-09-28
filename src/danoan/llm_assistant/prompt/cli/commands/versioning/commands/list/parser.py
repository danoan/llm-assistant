from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.prompt.cli import utils as cli_utils

import argparse


def __list__(*args, **kwargs):
    """
    List all tracked prompts.
    """
    entries = []
    for tp in api.get_tracked_prompts():
        entry = f"{tp.name}: @{tp.current_tag}"
        entries.append(entry)
    cli_utils.print_panel_list("Tracked Prompts", entries)


def extend_parser(subparser_action=None):
    command_name = "list"
    description = __list__.__doc__
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

    parser.set_defaults(func=__list__, subcommand_help=parser.print_help)

    return parser
