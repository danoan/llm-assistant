from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.runner.cli import utils as cli_utils
from danoan.llm_assistant.common.config import LLM_ASSISTANT_ENV_VARIABLE

import argparse
import logging

setup_logging()
logger = logging.getLogger(__name__)


def __init_llm_assistant__(
    reset: bool = False, use_env_var: bool = False, *args, **kwargs
):
    """
    Initialize llm-assistant configuration.

    It creates the configuration file in the location pointed
    by the environment variable LLM_ASSISTANT_CONFIGURATION_FOLDER.
    """
    from danoan.llm_assistant.runner.cli.commands.setup.setup_commands import init as M

    cli_utils.ensure_environment_variable_is_defined(logger)
    M.init(reset=reset, use_env_var=use_env_var)


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

    parser.add_argument(
        "--env",
        dest="use_env_var",
        action="store_true",
        help=f"Creates configuration file in the directory pointed by the environment variable {LLM_ASSISTANT_ENV_VARIABLE}",
    )
    parser.add_argument(
        "--force",
        dest="reset",
        action="store_true",
        help="Rewrites the configuration file",
    )
    parser.set_defaults(func=__init_llm_assistant__, subcommand_help=parser.print_help)

    return parser
