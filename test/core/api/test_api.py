from danoan.llm_assistant.core import api, model

import pytest

from dataclasses import asdict
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import toml
from functools import wraps

SCRIPT_FOLDER = Path(__file__).parent
INPUT_FOLDER = SCRIPT_FOLDER / "input"
CACHE_FILE = SCRIPT_FOLDER / "cache" / "test-api-cache"


def configuration_context(openai_key):
    config = api.Configuration(openai_key, True, str(CACHE_FILE.resolve()))

    def inner(func):
        @wraps(func)
        def wrapper():
            with TemporaryDirectory() as config_folder:
                os.environ[api.LLM_ASSISTANT_ENV_VARIABLE] = config_folder
                config_filepath = Path(config_folder).resolve() / "config.toml"

                with open(config_filepath, "w") as f_out:
                    toml.dump(asdict(config), f_out)

                load_config = api.get_configuration()
                func(load_config)

        return wrapper

    return inner


@pytest.mark.parametrize(
    "prompt_folder,prompt_input_file,prompt_expected_file",
    [
        (
            INPUT_FOLDER / "copywriter" / "prompts",
            INPUT_FOLDER / "copywriter" / "input" / "painting.toml",
            INPUT_FOLDER / "copywriter" / "expected" / "painting.toml",
        )
    ],
)
def test_custom(openai_key, prompt_folder, prompt_input_file, prompt_expected_file):
    @configuration_context(openai_key)
    def inner(config):
        system_prompt_file = prompt_folder / "system.txt.tpl"
        user_prompt_file = prompt_folder / "user.txt.tpl"
        with open(system_prompt_file) as f_sys, open(user_prompt_file) as f_usr:
            system_prompt = f_sys.read()
            user_prompt = f_usr.read()

            prompt_configuration = model.PromptConfiguration(
                "complete-the-sentence", system_prompt, user_prompt
            )

        with open(prompt_input_file) as f_in, open(prompt_expected_file) as f_exp:
            data = toml.load(f_in)
            expected_data = toml.load(f_exp)
            r = api.custom(prompt_configuration, model="gpt-3.5-turbo", **data)
            assert r
            assert r.content
            assert r.content == expected_data["content"]

    inner()
