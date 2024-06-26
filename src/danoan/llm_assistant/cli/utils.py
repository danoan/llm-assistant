from danoan.llm_assistant.core import api, exception, model

import toml
from pathlib import Path
from typing import Any, Tuple


def ensure_environment_variable_is_defined(logger):
    try:
        api.get_configuration_folder()
    except exception.EnvironmentVariableNotDefinedError:
        logger.error(
            f"The environment variable {api.LLM_ASSISTANT_ENV_VARIABLE} is not defined. Please define it before proceeding."
        )
        exit(1)


def ensure_configuration_file_exist(logger):
    ensure_environment_variable_is_defined(logger)
    try:
        api.get_configuration()
    except exception.ConfigurationFileDoesNotExistError:
        logger.error(
            f"The file {api.get_configuration_filepath()} was not found. You can create one by calling llm-assistant setup init"
        )
        exit(1)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def value_or_default(data_dict, key, default: Any):
    if key in data_dict:
        return data_dict[key]
    else:
        return default


def is_a_prompt_config_file(
    filepath: Path,
) -> Tuple[bool, model.PromptConfiguration]:
    try:
        o = toml.load(filepath)
        prompt_config = model.PromptConfiguration(**o)
        return True, prompt_config
    except toml.TomlDecodeError as ex:
        raise ex
    except ValueError:
        return False, None
