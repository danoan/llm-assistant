from danoan.llm_assistant.runner.core import api, model

import pytest

from pathlib import Path
import toml

SCRIPT_FOLDER = Path(__file__).parent
INPUT_FOLDER = SCRIPT_FOLDER / "input"
CACHE_FILE = SCRIPT_FOLDER / "cache" / "test-api-cache"


@pytest.mark.api
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
    # TODO: When executing via pytest, this test raises an error within
    # the lang-chain library. If I remove the cache, it works.
    # The same behaviour is not observed if executed out of pytest
    config = model.LLMAssistantConfiguration(
        openai_key, "gpt-3.5-turbo", True, str(CACHE_FILE.resolve())
    )

    api.LLMAssistant().setup(config)

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
        r = api.custom(prompt_configuration, **data)
        assert r
        assert r.content
        assert r.content == expected_data["content"]
