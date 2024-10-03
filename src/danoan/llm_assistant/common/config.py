from danoan.llm_assistant.common import exception, model


from functools import lru_cache
import logging
import os
from pathlib import Path
import sys
import toml
from typing import Optional

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
LLM_ASSISTANT_CONFIGURATION_FILENAME = "llma-assistant-config.toml"


@lru_cache
def _get_first_configuration_filepath_within_file_hierarchy(
    base_dir: Path,
) -> Optional[Path]:
    """
    Traverses the parents of the working directory until
    the configuration file is found.
    """
    visited = set()
    folders_to_visit = [base_dir]
    while len(folders_to_visit) > 0:
        cur_folder = folders_to_visit.pop()
        if cur_folder in visited:
            break
        visited.add(cur_folder)
        folders_to_visit.append(cur_folder.parent)
        for p in cur_folder.iterdir():
            if not p.is_dir():
                if p.name == LLM_ASSISTANT_CONFIGURATION_FILENAME:
                    return p
                continue
    return None


def get_configuration_folder() -> Path:
    """
    Return directory where configuration file is stored.

    First checks if a configuration file exists in the file hierarchy.
    If that is the case, return the directory where the configuration file
    is located.

    If the procedure above does not find a configuration file, return the
    value stored in the environment variable LLM_ASSISTANT_ENV_VARIABLE.

    If the environment variable is not defined, raise an error.

    Raises:
        EnvironmentVariableNotDefinedError: If the LLM_ASSISTANT_ENV_VARIABLE
                                            is not defined and a configuration file
                                            is not found in the file hierarchy
    """
    config_filepath = _get_first_configuration_filepath_within_file_hierarchy(
        Path(os.getcwd())
    )
    if config_filepath:
        return config_filepath.parent

    if LLM_ASSISTANT_ENV_VARIABLE in os.environ:
        return Path(os.environ[LLM_ASSISTANT_ENV_VARIABLE]).expanduser()

    raise exception.EnvironmentVariableNotDefinedError()


def get_configuration_filepath() -> Path:
    """
    Return path to llm-assistant configuration file.
    """
    return get_configuration_folder() / LLM_ASSISTANT_CONFIGURATION_FILENAME


def get_configuration() -> model.LLMAssistantConfiguration:
    """
    Return configuration object.
    """
    config_filepath = get_configuration_filepath()
    if not config_filepath.exists():
        raise exception.ConfigurationFileDoesNotExistError()

    with open(config_filepath, "r") as f:
        return model.LLMAssistantConfiguration(**toml.load(f))


def get_prompt_configuration(prompt_name: str) -> model.PromptConfiguration:
    """
    Get prompt configuration object.

    It searches the prompt configuration file within the directory specified
    by runner.local_folder setting.

    Raises:
        FileNotFoundError: if prompt configuration file is not found.
    """
    config = get_configuration()
    prompt_config_filepath = config.runner.local_folder / prompt_name / "config.toml"
    if not prompt_config_filepath.exists():
        raise FileNotFoundError(2, "File not found", prompt_config_filepath)
    with open(prompt_config_filepath) as f:
        return model.PromptConfiguration(**toml.load(f))
