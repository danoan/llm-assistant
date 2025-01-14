from pathlib import Path
from typing import Any, Tuple

import toml

from danoan.llm_assistant.common import config, exception, model
from danoan.llm_assistant.runner.core import api


def ensure_environment_variable_is_defined(logger):
    # Not necessqry anymore
    pass
    # try:
    #     config.get_configuration_folder()
    # except exception.EnvironmentVariableNotDefinedError:
    #     logger.error(
    #         f"The environment variable {api.LLM_ASSISTANT_ENV_VARIABLE} is not defined. Please define it before proceeding."
    #     )
    #     exit(1)


def ensure_configuration_file_exists(logger):
    ensure_environment_variable_is_defined(logger)
    try:
        config.get_configuration()
    except exception.ConfigurationFileDoesNotExistError:
        logger.error(
            f"The file {config.get_configuration_filepath()} was not found. You can create one by calling llm-assistant setup init"
        )
        exit(1)


def ensure_prompt_exists(prompt_name: str, logger):
    llma_config = config.get_configuration()

    if not llma_config.prompt:
        logger.error("Prompt settings are not specified")
        exit(1)

    prompt_config_filepath = (
        config.get_configuration_folder()
        / llma_config.prompt.prompt_collection_folder
        / prompt_name
        / "config.toml"
    )
    if not prompt_config_filepath.exists():
        logger.error(
            f"Could not find the configuration file for prompt {prompt_name}. It should be located at {prompt_config_filepath}"
        )
        exit(1)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "-")


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
