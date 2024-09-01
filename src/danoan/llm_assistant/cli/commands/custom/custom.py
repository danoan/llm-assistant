from danoan.llm_assistant.core import api, model

import logging
from pathlib import Path
import sys
import json
import toml
from typing import TextIO

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def custom(prompt_configuration_filepath: Path, prompt_instance_data: TextIO):
    config = api.get_configuration()
    api.LLMAssistant().setup(config)

    with open(prompt_configuration_filepath, "r") as file_pc:
        prompt_configuration = model.PromptConfiguration(**toml.load(file_pc))
        prompt_instance = json.load(prompt_instance_data)

        response = api.custom(prompt_configuration, **prompt_instance)
        return response
