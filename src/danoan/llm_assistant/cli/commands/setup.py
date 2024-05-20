from danoan.llm_assistant.cli.commands.setup_commands import init

import argparse


def extend_parser(subparser_action=None):
    command_name = "setup"
    description = "Configure LLM assistant."
    help = description.split(".")[0] if description else ""

    if subparser_action:
        parser = subparser_action.add_parser(
            command_name, help=help, description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    else:
        parser = argparse.ArgumentParser(
            command_name, description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

    subparser_action = parser.add_subparsers()
    list_of_commands = [init]
    for command in list_of_commands:
        command.extend_parser(subparser_action)

    return parser
