from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.prompt.cli import utils as cli_utils

from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.common.model import RunnerConfiguration
from danoan.llm_assistant.runner.core import api as llma

import json


def __run_tests__(runner_configuration: RunnerConfiguration, prompt_name: str):
    llma.LLMAssistant().setup(runner_configuration)
    prompt_config = common.get_prompt_configuration(prompt_name)
    regression_fp = api.get_prompt_test_regression_filepath(prompt_name)

    with open(regression_fp, "r") as fi:
        input_obj = json.load(fi)

        for entry in input_obj:
            response = llma.custom(prompt_config, **entry["input"])
            response_obj = json.loads(response.content)

            response_str = json.dumps(response_obj, ensure_ascii=False, indent=2)
            expected_str = json.dumps(entry["output"], ensure_ascii=False, indent=2)

            yield (response_str, expected_str)


def run_tests(prompt_name: str):
    try:
        for response_str, expected_str in __run_tests__(
            common.get_configuration().runner, prompt_name
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
