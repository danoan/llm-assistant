from danoan.llm_assistant.prompt.cli.commands.init import parser as init
from danoan.llm_assistant.prompt.cli.commands.list import parser as list_prompts
from danoan.llm_assistant.prompt.cli.commands.push import parser as push
from danoan.llm_assistant.prompt.cli.commands.track import parser as track

import argparse


def extend_parser(subparser_action=None):
    command_name = "versioning"
    description = "Collection of tools for prompt versioning"
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

    subparser_action = parser.add_subparsers()
    list_of_commands = [init, list_prompts, push, track]
    for command in list_of_commands:
        command.extend_parser(subparser_action)

    parser.set_defaults(subcommand_help=parser.print_help)

    return parser
