from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.prompt.cli import utils as cli_utils

from danoan.llm_assistant.runner.core import api as llma
from danoan.llm_assistant.runner.core.model import PromptConfiguration

import argparse
import json
import toml


def __run_tests__(prompt_name: str, *args, **kwargs):
    """
    Run tests for a prompt and generate a report.
    """
    llma.LLMAssistant().setup(cli_utils.get_llma_configuration())
    try:
        prompt_config_fp, input_fp, expected_fp = api.get_prompt_test_files(prompt_name)

        prompt_config = None
        with open(prompt_config_fp, "r") as f:
            prompt_config = PromptConfiguration(**toml.load(f))

        with open(input_fp, "r") as fi, open(expected_fp, "r") as fe:
            input_obj = json.load(fi)
            expected_obj = json.load(fe)

            for entry_in, entry_exp in zip(input_obj, expected_obj):
                response = llma.custom(prompt_config, **entry_in)
                response_obj = json.loads(response.content)

                response_str = json.dumps(response_obj, ensure_ascii=False, indent=2)
                expected_str = json.dumps(entry_exp, ensure_ascii=False, indent=2)
                cli_utils.print_side_by_side(
                    response_str,
                    expected_str,
                    left_title="New response",
                    right_title="Previous response",
                )

    except FileNotFoundError:
        print(f"Could not open the test folder for prompt: {prompt_name}")
        exit(1)


def extend_parser(subparser_action=None):
    command_name = "run-tests"
    description = __run_tests__.__doc__
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

    parser.add_argument("prompt_name", type=str)
    parser.set_defaults(func=__run_tests__, subcommand_help=parser.print_help)

    return parser
