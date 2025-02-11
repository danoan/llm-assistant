from danoan.llm_assistant.common.model import RunnerConfiguration

from danoan.llm_assistant.common import config
from danoan.llm_assistant.prompt.cli import utils as cli_utils
from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.runner.core import api as llma

import json
import logging
import sys

logger = logging.getLogger(__file__)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def __run_tests__(runner_configuration: RunnerConfiguration, prompt_name: str):
    llma.LLMAssistant().setup(runner_configuration)
    prompt_config = config.get_prompt_configuration(prompt_name)

    test_model = api.get_prompt_test_regression_filepath(prompt_name)
    test_run = test_model.parent / runner_configuration.model / test_model.name
    if not test_run.exists():
        logger.error(
            f"No test run file for prompt {prompt_config.name} and model {runner_configuration.model} was generated yet. You need to generate one first using the rengerate-tests command."
        )
        exit(1)

    with open(test_run, "r") as fi:
        input_obj = json.load(fi)

        for entry in input_obj:
            response = llma.custom(prompt_config, **entry["input"])
            try:
                response_obj = json.loads(response.content)
            except:
                response_obj = response.content

            response_str = json.dumps(response_obj, ensure_ascii=False, indent=2)
            expected_str = json.dumps(entry["output"], ensure_ascii=False, indent=2)

            yield (response_str, expected_str)


def run_tests(prompt_name: str):
    try:
        for response_str, expected_str in __run_tests__(
            config.get_configuration().runner, prompt_name
        ):
            cli_utils.print_side_by_side(
                response_str,
                expected_str,
                left_title="New response",
                right_title="Previous response",
            )
    except FileNotFoundError as ex:
        print(ex)
        exit(1)
