import copy
import logging
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Generator, Literal, Optional

import git
import toml
from danoan.llm_assistant.common.model import PromptRepositoryConfiguration

from danoan.llm_assistant.common import config
from danoan.llm_assistant.prompt.core import model

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
    llma_config = config.get_configuration()
    return llma_config.prompt.local_folder


def get_prompt_configuration_filepath(prompt_name: str) -> Path:
    return get_prompts_folder() / prompt_name / "config.toml"


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
            logger.debug(key)
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
    return model.TrackedPrompt(
        repository_name, repository_folder, current_tag, branches
    )


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


def get_prompt_test_regression_filepath(prompt_name: str) -> Path:
    """
    Get regression test file.
    """
    return get_prompts_folder() / prompt_name / "tests" / "regression.json"


def sync(repo_config: PromptRepositoryConfiguration, progress_callback=None):
    class Events(Enum):
        SYNC_CONFIG = "sync_config"
        FETCH = "fetch"
        CHECKOUT = "checkout"
        SYNCED = "synced"
        SYNC_LOCAL_FOLDER = "sync_local_folder"
        NOT_TRACKED = "not_tracked"
        NOT_PROMPT_REPOSITORY = "not_prompt_repository"
        GIT = "git"
        ITEM = "item"
        BEGIN = "begin"
        END = "end"

    @dataclass
    class SyncItem:
        event: Literal[
            Events.SYNC_CONFIG,
            Events.FETCH,
            Events.CHECKOUT,
            Events.SYNCED,
            Events.SYNC_LOCAL_FOLDER,
            Events.NOT_TRACKED,
            Events.NOT_PROMPT_REPOSITORY,
            Events.GIT,
            Events.ITEM,
            Events.BEGIN,
            Events.END,
        ]
        name: Optional[str] = None
        value: Optional[str] = None

    def _progress_callback(sync_item: SyncItem):
        if progress_callback:
            d = asdict(sync_item)
            d["event"] = sync_item.event.value
            progress_callback(**d)
        else:
            return

    def _git_progress_callback(op_code, cur_count, max_count=None, message=""):
        _progress_callback(SyncItem(Events.GIT))
        _progress_callback(SyncItem(Events.BEGIN))
        _progress_callback(SyncItem(Events.ITEM, "op_code", op_code))
        _progress_callback(SyncItem(Events.ITEM, "cur_count", cur_count))
        _progress_callback(SyncItem(Events.ITEM, "max_count", max_count))
        _progress_callback(SyncItem(Events.ITEM, "message", message))
        _progress_callback(SyncItem(Events.END))

    # Sync prompt repository configuration
    _progress_callback(SyncItem(Events.SYNC_CONFIG))
    for prompt_name, version in repo_config.versioning.items():
        _progress_callback(SyncItem(Events.SYNC_CONFIG, "prompt_name", prompt_name))
        _progress_callback(SyncItem(Events.SYNC_CONFIG, "version", version))
        prompt_folder = get_prompts_folder() / prompt_name
        prompt_repo_url = f"git@github.com:{repo_config.git_user}/{prompt_name}.git"
        repo = None
        if not prompt_folder.exists():
            _progress_callback(SyncItem(Events.FETCH, "prompt", prompt_repo_url))
            repo = git.Repo.clone_from(
                prompt_repo_url, prompt_folder, progress=_git_progress_callback
            )
        else:
            repo = git.Repo(prompt_folder)

        _progress_callback(SyncItem(Events.CHECKOUT, "version", version))
        repo.git.checkout(version)

    # Sync prompt repository local folder
    updated_repo_config = copy.deepcopy(repo_config)
    _progress_callback(SyncItem(Events.SYNC_LOCAL_FOLDER))
    for prompt_folder in repo_config.local_folder.iterdir():
        _progress_callback(SyncItem(Events.SYNC_LOCAL_FOLDER, "folder", prompt_folder))
        if is_prompt_repository(prompt_folder):
            prompt_name = prompt_folder.stem
            if prompt_name not in repo_config.versioning.keys():
                tp = get_tracked_prompt(prompt_name)
                updated_repo_config.versioning[prompt_name] = tp.current_tag
                _progress_callback(
                    SyncItem(Events.NOT_TRACKED, "version", tp.current_tag)
                )
            else:
                _progress_callback(SyncItem(Events.SYNCED))
        else:
            _progress_callback(SyncItem(Events.NOT_PROMPT_REPOSITORY))

    llma_config = config.get_configuration()
    llma_config.prompt = updated_repo_config

    with open(config.get_configuration_filepath(), "w") as f:
        toml.dump(llma_config.__asdict__(), f)
