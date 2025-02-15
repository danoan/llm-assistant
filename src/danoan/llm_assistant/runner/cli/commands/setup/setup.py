from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.common import config, exception
from danoan.llm_assistant.runner.cli.commands.setup.setup_commands import (
    init_parser as init,
)

import argparse
import logging

setup_logging()
logger = logging.getLogger(__name__)


def __setup__(*args, **kwargs):
    try:
        print(
            f"The environment variable {config.LLM_ASSISTANT_ENV_VARIABLE}"
            f" is set to: {config.get_environment_variable_value()}"
        )
    except exception.EnvironmentVariableNotDefinedError:
        logger.error(
            f"The environment variable: {config.LLM_ASSISTANT_ENV_VARIABLE} is not set"
        )
        exit(1)

    print(
        f"The configuration file being used is located at: {config.get_configuration_filepath()}\n"
    )
    print(config.get_configuration())


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
