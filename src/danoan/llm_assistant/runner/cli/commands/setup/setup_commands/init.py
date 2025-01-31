import logging
import os
import sys

from pathlib import Path
import toml

from danoan.llm_assistant.common import config
from danoan.llm_assistant.common import model

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def __create_configuration_model__():
    runner_config = model.RunnerConfiguration(
        "openai-key", "openai-model", True, "path to the cache file"
    )
    repo_config = model.PromptRepositoryConfiguration(
        "git-namespace-prompt-repository",
        "local folder where prompts are stored",
        {"my-prompt": "1.0.0"},
    )
    return model.LLMAssistantConfiguration(runner_config, repo_config)


def init(reset: bool = False, use_env_var: bool = False):
    if use_env_var:
        config_folder = config.get_configuration_folder()
        if not config_folder.exists():
            config_folder.mkdir(parents=True, exist_ok=True)

        config_path = config.get_configuration_filepath()
    else:
        config_path = Path(os.getcwd()) / config.LLM_ASSISTANT_CONFIGURATION_FILENAME

    if config_path.exists() and not reset:
        print(f"The configuration file: {config_path} exists already.")

    if config_path.exists() and reset:
        print(f"Reseting the current configuration file: {config_path}.")

    if not config_path.exists() or reset:
        llma_config = __create_configuration_model__()
        with open(config_path, "w") as f:
            toml.dump(llma_config.__asdict__(), f)
