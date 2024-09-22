from danoan.llm_assistant.prompt.cli.commands.evaluate.commands.regenerate_tests import (
    parser as regenerate_tests,
)
from danoan.llm_assistant.prompt.cli.commands.evaluate.commands.run_tests import (
    parser as run_tests,
)

import argparse


def extend_parser(subparser_action=None):
    command_name = "evaluate"
    description = "Collection of tools to evaluate prompts"
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
    list_of_commands = [regenerate_tests, run_tests]
    for command in list_of_commands:
        command.extend_parser(subparser_action)

    parser.set_defaults(subcommand_help=parser.print_help)

    return parser
