from danoan.llm_assistant.common.model import (
    RunnerConfiguration,
    PromptRepositoryConfiguration,
)
from danoan.llm_assistant.common.config import get_absolute_configuration_path

from copy import deepcopy


def generate_absolute_runner_config(runner_config: RunnerConfiguration):
    """
    Resolve all paths in the runner configuration to absolute paths.

    This requires llm-assistant-config.toml to be defined.
    """
    runner_config_copy = deepcopy(runner_config)
    runner_config_copy.cache_path = get_absolute_configuration_path(
        runner_config_copy.cache_path
    )

    return runner_config_copy


def generate_absolute_prompt_config(prompt_repo_config: PromptRepositoryConfiguration):
    """
    Resolve all paths in the prompt repository configuration to absolute paths.

    This requires llm-assistant-config.toml to be defined.
    """
    prompt_repo_config_copy = deepcopy(prompt_repo_config)
    prompt_repo_config_copy.prompt_collection_folder = get_absolute_configuration_path(
        prompt_repo_config_copy.prompt_collection_folder
    )

    return prompt_repo_config_copy
