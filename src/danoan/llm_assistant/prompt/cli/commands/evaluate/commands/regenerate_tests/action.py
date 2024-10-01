from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.runner.core import api as runner

from danoan.llm_assistant.prompt.core import api

import json
from typing import Any


def __regenerate_tests__(prompt_name: str) -> Any:
    runner.LLMAssistant().setup(common.get_configuration().runner)
    prompt_config = common.get_prompt_configuration(prompt_name)

    regression_test_fp = api.get_prompt_test_regression_filepath(prompt_name)
    updated_data = None
    with open(regression_test_fp, "r") as f:
        data = json.load(f)
        for entry in data:
            response = runner.custom(prompt_config, **entry["input"])
            entry["output"] = json.loads(response.content)

        updated_data = data

    with open(regression_test_fp, "w") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    return updated_data


def regenerate_tests(prompt_name: str):
    print(__regenerate_tests__(prompt_name))
