from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.common import model
from danoan.llm_assistant.runner.core import api

import json
import logging
from typing import List, Optional, TextIO

setup_logging()
logger = logging.getLogger(__name__)


def run(
    runner_configuration: model.RunnerConfiguration,
    prompt: model.PromptConfiguration,
    prompt_input: TextIO,
    prompt_param: Optional[List[List[str]]],
):
    api.LLMAssistant().setup(runner_configuration)

    input_obj = json.load(prompt_input)
    if prompt_param:
        for key, value in prompt_param:
            input_obj[key] = value

    return api.custom(prompt, **input_obj)
