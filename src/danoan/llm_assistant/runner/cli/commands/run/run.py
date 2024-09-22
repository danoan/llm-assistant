from danoan.llm_assistant.runner.core import api
from danoan.llm_assistant.runner.core import model


import json
from typing import List, Optional, TextIO


def run(
    llma_configuration: model.LLMAssistantConfiguration,
    prompt: model.PromptConfiguration,
    prompt_input: TextIO,
    prompt_param: Optional[List[List[str]]],
):
    api.LLMAssistant().setup(llma_configuration)

    input_obj = json.load(prompt_input)
    if prompt_param:
        for key, value in prompt_param:
            input_obj[key] = value

    return api.custom(prompt, **input_obj)
