from danoan.llm_assistant.common import model
from danoan.llm_assistant.runner.core import api


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
