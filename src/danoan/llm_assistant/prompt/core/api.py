from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.prompt.core import model

import git
import logging
from pathlib import Path
import sys
import toml
from typing import Generator

logger = logging.getLogger(__file__)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def get_prompts_folder() -> Path:
    """
    Return path to the folder where all tracked prompts are located.
    """
    config = common.get_configuration()
    return Path(config.prompt_repository["path"])


def is_prompt_repository(path: Path) -> bool:
    """
    Check if a path points to a prompt repository.

    A prompt repository must contain a `config.toml`
    that contains some mandatory keys.
    """
    configuration_prompt_path = path / "config.toml"
    if not configuration_prompt_path.exists():
        return False
    logger.debug(f"Loading: {configuration_prompt_path}")
    obj = toml.load(configuration_prompt_path)
    mandatory_keys = ["user_prompt", "system_prompt"]
    for key in mandatory_keys:
        if key not in obj:
            logger.debug(obj)
            return False
    return True


def get_tracked_prompt(repository_name: str) -> model.TrackedPrompt:
    """
    Return a TrackedPrompt from the prompt repository.

    Raises:
        FileNotFoundError if prompt does not exist.
    """
    repository_folder = get_prompts_folder() / repository_name
    if not repository_folder.exists():
        raise FileNotFoundError()
    repository = git.Repo(repository_folder)
    if repository.head.is_valid():
        current_commit = repository.head.commit
        current_tag = "no-tag"
        for tag in repository.tags:
            if tag.commit == current_commit:
                current_tag = tag.name
        branches = [b for b in repository.branches if b.name not in ["master"]]
    return model.TrackedPrompt(repository_name, repository_folder, current_tag, branches)


def get_tracked_prompts() -> Generator[model.TrackedPrompt, None, None]:
    """
    Return a list of all prompts tracked by the tool.

    A prompt is considered tracked if it is a prompt repository located
    at `get_prompts_folder`.

    A prompt repository is a folder with a `config.toml` file that
    can be loaded as a PromptConfiguration.
    """
    prompts_folder = get_prompts_folder()
    for x in prompts_folder.iterdir():
        if not is_prompt_repository(x):
            continue
        yield get_tracked_prompt(x.name)


def get_prompt_test_files(prompt_name: str):
    """ """
    prompt_folder = get_prompts_folder() / prompt_name
    if not prompt_folder.exists():
        raise FileNotFoundError()

    prompt_config = prompt_folder / "config.toml"
    input = prompt_folder / "tests" / "regression" / "input.json"
    expected = prompt_folder / "tests" / "regression" / "expected.json"

    return prompt_config, input, expected
