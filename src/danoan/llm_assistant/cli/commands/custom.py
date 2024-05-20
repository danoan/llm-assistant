from danoan.llm_assistant.core import api, exception, model

import argparse
import logging
from pathlib import Path
import sys
import toml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def __custom__(prompt_configuration_filepath: str, prompt_instance_filepath: str, *args, **kwargs):
    api.ensure_configuration_file_exist(logger)
    prompt_configuration_filepath = Path(prompt_configuration_filepath)
    if not prompt_configuration_filepath.exists():
        logger.error(
            f"The prompt configuration file: {prompt_configuration_filepath} does not exist")
        exit(1)

    prompt_instance_filepath = Path(prompt_instance_filepath)
    if not prompt_instance_filepath.exists():
        logger.error(
            f"The prompt instance file: {prompt_configuration_filepath} does not exist")
        exit(1)

    with open(prompt_configuration_filepath, "r") as file_pc, open(prompt_instance_filepath, "r") as file_pi:
        prompt_configuration = model.PromptConfiguration(**toml.load(file_pc))
        prompt_instance = toml.load(file_pi)

        response = api.custom(prompt_configuration, **prompt_instance)
        print(response)


def extend_parser(subparser_action=None):
    command_name = "custom"
    description = api.custom.__doc__
    help = description.split(".")[0] if description else ""

    if subparser_action:
        parser = subparser_action.add_parser(
            command_name, help=help, description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    else:
        parser = argparse.ArgumentParser(
            command_name, description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("prompt_configuration_filepath",
                        help="Path to toml prompt configuration file")
    parser.add_argument("prompt_instance_filepath",
                        help="Path to toml containing prompt variable values.")
    parser.set_defaults(func=__custom__)

    return parser
