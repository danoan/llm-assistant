from danoan.llm_assistant.runner.cli import utils as cli_utils

import argparse
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def __init_llm_assistant__(*args, **kwargs):
    """
    Initialize llm-assistant configuration.

    It creates the configuration file in the location pointed
    by the environment variable LLM_ASSISTANT_CONFIGURATION_FOLDER.
    """
    from danoan.llm_assistant.runner.cli.commands.setup.setup_commands import init as M

    cli_utils.ensure_environment_variable_is_defined(logger)
    M.init()


def extend_parser(subparser_action=None):
    command_name = "init"
    description = __init_llm_assistant__.__doc__
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

    parser.set_defaults(func=__init_llm_assistant__, subcommand_help=parser.print_help)

    return parser
