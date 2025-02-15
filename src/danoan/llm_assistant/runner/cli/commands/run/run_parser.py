from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.runner.cli import utils as cli_utils
from danoan.llm_assistant.common import config as config


import argparse
import io
import json
import logging
import sys
from typing import List, Optional, TextIO

setup_logging()
logger = logging.getLogger(__name__)


def __run__(
    prompt_name: str,
    prompt_input: TextIO,
    from_text: Optional[str] = None,
    prompt_param: Optional[List[List[str]]] = None,
    *args,
    **kwargs,
):
    """
    Run a pre-registered prompt.
    """
    from danoan.llm_assistant.runner.cli.commands.run import run as M

    cli_utils.ensure_configuration_file_exists(logger)
    cli_utils.ensure_prompt_exists(prompt_name, logger)
    llma_config = config.get_configuration()

    prompt = config.get_prompt_configuration(prompt_name)
    ss = prompt_input
    if from_text:
        ss = io.StringIO()
        json.dump(json.loads(from_text), ss, ensure_ascii=False)
        ss.seek(0)

    response = M.run(llma_config.runner, prompt, ss, prompt_param)
    try:
        obj = json.loads(response.content)
        json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    except Exception:
        wrapped = [response.content]
        json.dump(wrapped[0], sys.stdout, indent=2, ensure_ascii=False)


def extend_parser(subparser_action=None):
    command_name = "run"
    description = __run__.__doc__
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

    parser.add_argument("prompt_name", type=str, help="Name of the prompt to run")
    parser.add_argument(
        "--prompt-param",
        "--p",
        nargs=2,
        action="append",
        type=str,
        help="Key value pair specifing one parameter accepted by the prompt",
    )

    meg = parser.add_mutually_exclusive_group()
    meg.add_argument(
        "--from-text",
        type=str,
        help="Prompt parameters passed as a JSON object encoded as string",
    )
    meg.add_argument(
        "prompt_input",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Prompt input in json format",
    )

    parser.set_defaults(func=__run__, subcommand_help=parser.print_help)

    return parser
