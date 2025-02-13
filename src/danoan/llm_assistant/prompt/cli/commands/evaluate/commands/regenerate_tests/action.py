from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.common import config
from danoan.llm_assistant.common import utils
from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.runner.core import api as runner
from danoan.llm_assistant.runner.core import api as llma

from copy import deepcopy
import json
import logging
import sys
from typing import Any

setup_logging()
logger = logging.getLogger(__name__)


def __regenerate_tests__(prompt_name: str) -> Any:
    runner_configuration = config.get_configuration().runner
    runner.LLMAssistant().setup(
        utils.generate_absolute_runner_config(runner_configuration)
    )
    prompt_config = config.get_prompt_configuration(prompt_name)

    test_model = api.get_prompt_test_regression_filepath(prompt_name)
    test_run_fp = test_model.parent / runner_configuration.model / test_model.name

    test_run_fp.parent.mkdir(parents=True, exist_ok=True)

    output_obj = []
    with open(test_model, "r") as fi:
        input_obj = json.load(fi)

        for entry in input_obj:
            response = llma.custom(prompt_config, **entry["input"])

            try:
                response_obj = json.loads(response.content)
            except:
                response_obj = response.content

            output_entry = deepcopy(entry)
            output_entry["output"] = response_obj
            output_obj.append(output_entry)

    with open(test_run_fp, "w") as fo:
        json.dump(output_obj, fo, ensure_ascii=False, indent=2)

    return output_obj


def regenerate_tests(prompt_name: str):
    json.dump(
        __regenerate_tests__(prompt_name), sys.stdout, ensure_ascii=False, indent=2
    )
