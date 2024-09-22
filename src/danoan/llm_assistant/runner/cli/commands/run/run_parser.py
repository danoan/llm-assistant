from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.runner.core import api

from danoan.llm_assistant.runner.cli.commands.run import run as M
from danoan.llm_assistant.runner.cli import utils as cli_utils


import argparse
import io
import json
import logging
import sys
from typing import List, Optional, TextIO

logger = logging.getLogger(__file__)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def __run__(
    prompt_name: str,
    prompt_input: TextIO,
    from_text: Optional[str] = None,
    prompt_param: Optional[List[List[str]]] = None,
    *args,
    **kwargs,
):
    cli_utils.ensure_configuration_file_exists(logger)
    cli_utils.ensure_prompt_exists(prompt_name, logger)
    api.LLMAssistant().setup(common.get_configuration())
    llma_config = api.LLMAssistant().config

    prompt = common.get_prompt_configuration(prompt_name)
    ss = prompt_input
    if from_text:
        ss = io.StringIO()
        json.dump(json.loads(from_text), ss, ensure_ascii=False)
        ss.seek(0)

    response = M.run(llma_config, prompt, ss, prompt_param)
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
