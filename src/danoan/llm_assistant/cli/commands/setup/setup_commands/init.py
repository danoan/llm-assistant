from danoan.llm_assistant.core import api, model
from danoan.llm_assistant.cli import utils

import argparse
from dataclasses import asdict
import logging
import sys
import toml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def init(reset: bool = False):
    """
    Initialize llm-assistant configuration.

    It creates the configuration file in the location pointed
    by the environment variable LLM_ASSISTANT_CONFIGURATION_FOLDER.
    """
    config_folder = api.get_configuration_folder()
    if not config_folder.exists():
        config_folder.mkdir(parents=True, exist_ok=True)

    config_path = api.get_configuration_filepath()
    if not config_path.exists() or reset:
        config = model.LLMAssistantConfiguration()
        with open(config_path, "w") as f:
            toml.dump(asdict(config), f)


def __init_llm_assistant__(*args, **kwargs):
    utils.ensure_environment_variable_is_defined(logger)
    init()


def extend_parser(subparser_action=None):
    command_name = "init"
    description = init.__doc__
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
