from danoan.llm_assistant.core import api, model
from danoan.llm_assistant.cli import utils

import argparse
import logging
from pathlib import Path
import sys
import json
import toml
from typing import TextIO

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def custom(prompt_configuration_filepath: Path, prompt_instance_data: TextIO):
    with open(prompt_configuration_filepath, "r") as file_pc:
        prompt_configuration = model.PromptConfiguration(**toml.load(file_pc))
        prompt_instance = json.load(prompt_instance_data)

        response = api.custom(prompt_configuration, **prompt_instance)
        return response


def __custom__(
    prompt_configuration_filepath: str, prompt_instance_data: TextIO, *args, **kwargs
):
    utils.ensure_configuration_file_exist(logger)
    _prompt_configuration_filepath = Path(prompt_configuration_filepath)
    if not _prompt_configuration_filepath.exists():
        logger.error(
            f"The prompt configuration file: {prompt_configuration_filepath} does not exist"
        )
        exit(1)

    config = api.get_configuration()
    api.LLMAssistant().setup(config)
    response = custom(_prompt_configuration_filepath, prompt_instance_data)

    obj = json.loads(response.content)
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)


def extend_parser(subparser_action=None):
    command_name = "custom"
    description = api.custom.__doc__
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
        "prompt_configuration_filepath", help="Path to toml prompt configuration file"
    )
    parser.add_argument(
        "prompt_instance_data",
        type=argparse.FileType("r"),
        default=sys.stdin,
        nargs="?",
        help="Prompt data in JSON format",
    )
    parser.set_defaults(func=__custom__, subcommand_help=parser.print_help)

    return parser
