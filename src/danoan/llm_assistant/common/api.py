from danoan.llm_assistant.common import exception, model


from functools import lru_cache
import logging
import os
from pathlib import Path
import sys
import toml

logger = logging.getLogger(__file__)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

########################################
# Configuration files
########################################

LLM_ASSISTANT_ENV_VARIABLE = "LLM_ASSISTANT_CONFIGURATION_FOLDER"


def get_configuration_folder() -> Path:
    if LLM_ASSISTANT_ENV_VARIABLE not in os.environ:
        raise exception.EnvironmentVariableNotDefinedError()

    return Path(os.environ[LLM_ASSISTANT_ENV_VARIABLE]).expanduser()


@lru_cache
def get_configuration_filepath() -> Path:
    """
    Return path to llm-assistant configuration file.

    It traverses the parents of the working directory until
    the configuration file is found.

    If not found, checks if LLM_ASSISTANT_ENV_VARIABLE is
    defined and then use the configuration file located there.

    Raises:
        FileNotFoundError:                  if the configuration file is not found in
                                            the working directory.
        EnvironmentVariableNotDefinedError: If the LLM_ASSISTANT_ENV_VARIABLE
                                            is not defined
    """
    config_filename = "llm-assistant-config.toml"
    visited = set()
    folders_to_visit = [Path.cwd()]
    while len(folders_to_visit) > 0:
        cur_folder = folders_to_visit.pop()
        if cur_folder in visited:
            break
        visited.add(cur_folder)
        folders_to_visit.append(cur_folder.parent)
        for p in cur_folder.iterdir():
            if not p.is_dir():
                if p.name == config_filename:
                    return p
                continue

    return get_configuration_folder() / config_filename


def get_configuration() -> model.LLMAssistantConfiguration:
    config_filepath = get_configuration_filepath()

    if not config_filepath.exists():
        raise exception.ConfigurationFileDoesNotExistError()

    with open(config_filepath, "r") as f:
        return model.LLMAssistantConfiguration(**toml.load(f))


def get_prompt_configuration(prompt_name: str) -> model.PromptConfiguration:
    config = get_configuration()
    prompt_config_filepath = config.runner.local_folder / prompt_name / "config.toml"
    with open(prompt_config_filepath) as f:
        return model.PromptConfiguration(**toml.load(f))
