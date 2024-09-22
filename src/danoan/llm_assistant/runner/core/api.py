from danoan.llm_assistant.common import model
from danoan.llm_assistant.runner.core import exception

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import logging
import sys

logger = logging.getLogger(__file__)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


################################################################
# LLM Assistant Instance
################################################################


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

    def setup(self, config: model.RunnerConfiguration):
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


################################################################
# Commans
################################################################


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
