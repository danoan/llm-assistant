from danoan.llm_assistant.core import exception, model

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

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


LLM_ASSISTANT_ENV_VARIABLE = "LLM_ASSISTANT_CONFIGURATION_FOLDER"

################################################################
# Helper functions
################################################################


################################################################
# Configuration file
################################################################

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


# -------------------- LLM Assistant Instance --------------------


def _singleton(cls):
    instances_dict = {}

    def inner(*args, **kwargs):
        if cls not in instances_dict:
            instances_dict[cls] = cls(*args, **kwargs)
        return instances_dict[cls]

    return inner


@_singleton
class LLMAssistant:
    def __init__(self):
        self._config = None

    def setup(self, config: model.LLMAssistantConfiguration):
        self._config = config
        if self._config.use_cache:
            from langchain.globals import set_llm_cache
            from langchain_community.cache import SQLiteCache

            set_llm_cache(SQLiteCache(database_path=self._config.cache_path))

    @property
    def config(self) -> model.LLMAssistantConfiguration:
        if not self._config:
            raise exception.LLMAssistantNotConfiguredError
        return self._config


# -------------------- Commands --------------------


def custom(
    prompt_configuration: model.PromptConfiguration,
    **prompt_variables,
):
    """
    Execute a custom prompt.
    """
    instance = LLMAssistant()

    model = prompt_configuration.model
    if not model:
        model = instance.config.model

    llm = ChatOpenAI(
        api_key=instance.config.openai_key,
        model=model,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_configuration.system_prompt),
            ("user", prompt_configuration.user_prompt),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(prompt_variables)

    return response
