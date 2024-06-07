from danoan.llm_assistant.core import exception, model

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import os
from pathlib import Path
import toml

# -------------------- Configuration file --------------------

LLM_ASSISTANT_ENV_VARIABLE = "LLM_ASSISTANT_CONFIGURATION_FOLDER"


def get_configuration_folder() -> Path:
    if LLM_ASSISTANT_ENV_VARIABLE not in os.environ:
        raise exception.EnvironmentVariableNotDefinedError()

    return Path(os.environ[LLM_ASSISTANT_ENV_VARIABLE]).expanduser()


def get_configuration_filepath() -> Path:
    return get_configuration_folder() / "config.toml"


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
    model: str = "gpt-3.5-turbo",
    **prompt_variables,
):
    """
    Execute a custom prompt.
    """
    instance = LLMAssistant()

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
    return chain.invoke(prompt_variables)
