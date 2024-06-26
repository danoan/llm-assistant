from danoan.llm_assistant.core import api
from danoan.llm_assistant.cli.commands.setup.setup_commands import init

import argparse


def __setup__(*args, **kwargs):
    print(
        f"The environment variable {api.LLM_ASSISTANT_ENV_VARIABLE}"
        f" is set to: {api.get_configuration_folder()}"
    )
    print(f"The configuration file is located at: {api.get_configuration_filepath()}\n")
    print(api.get_configuration())


def extend_parser(subparser_action=None):
    command_name = "setup"
    description = "Configure LLM assistant."
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

    parser.set_defaults(func=__setup__, subcommand_help=parser.print_help)

    subparser_action = parser.add_subparsers()
    list_of_commands = [init]
    for command in list_of_commands:
        command.extend_parser(subparser_action)

    return parser
