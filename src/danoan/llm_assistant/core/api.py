from danoan.llm_assistant.core import model, exception

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from dataclasses import dataclass, asdict
import os
from pathlib import Path
import toml
from typing import Any, Dict, Optional

LLM_ASSISTANT_ENV_VARIABLE = "LLM_ASSISTANT_CONFIGURATION_FOLDER"


@dataclass
class Configuration:
    openai_key: Optional[str] = None
    use_cache: bool = False
    cache_path: Optional[str] = None

    def __str__(self):
        return (
            f"openai_key: <<HIDDEN>>\n"
            f"use_cache: {self.use_cache}\n"
            f"cache_path {self.cache_path}\n"
        )


def get_configuration_folder() -> Path:
    if LLM_ASSISTANT_ENV_VARIABLE not in os.environ:
        raise exception.EnvironmentVariableNotDefinedError()

    return Path(os.environ[LLM_ASSISTANT_ENV_VARIABLE]).expanduser()


def get_configuration_filepath() -> Path:
    return get_configuration_folder() / "config.toml"


def get_configuration() -> Configuration:
    config_filepath = get_configuration_filepath()

    if not config_filepath.exists():
        raise exception.ConfigurationFileDoesNotExistError()

    with open(config_filepath, "r") as f:
        return Configuration(**toml.load(f))


def ensure_configuration_file_exist(logger):
    try:
        get_configuration()
    except exception.EnvironmentVariableNotDefinedError:
        logger.error(
            f"The environment variable {LLM_ASSISTANT_ENV_VARIABLE} is not defined. Please define it before proceeding."
        )
        exit(1)
    except exception.ConfigurationFileDoesNotExistError:
        logger.error(
            f"The file {get_configuration_filepath()} was not found. You can create one by calling llm-assistant setup init"
        )
        exit(1)


def init(reset: bool = False):
    config_folder = get_configuration_folder()
    if not config_folder.exists():
        config_folder.mkdir(parents=True, exist_ok=True)

    config_path = get_configuration_filepath()
    if not config_path.exists() or reset:
        config = Configuration()
        with open(config_path, "w") as f:
            toml.dump(asdict(config), f)


def configure_lang_chain(config: Configuration, overwrite: bool = False):
    done = False

    def _config():
        nonlocal done
        if done and not overwrite:
            return True

        if config.use_cache:
            from langchain.globals import set_llm_cache
            from langchain_community.cache import SQLiteCache

            set_llm_cache(SQLiteCache(database_path=config.cache_path))

        done = True
        return True

    return _config()


# -------------------- Commands --------------------


def custom(
    prompt_configuration: model.PromptConfiguration,
    model="gpt-3.5-turbo",
    **prompt_variables,
):
    """
    Execute a custom prompt.
    """
    config = get_configuration()
    configure_lang_chain(config)

    llm = ChatOpenAI(
        api_key=config.openai_key,
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
