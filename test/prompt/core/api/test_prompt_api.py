from danoan.llm_assistant.prompt.core import api, model, utils

from danoan.llm_assistant.common.config import (
    LLM_ASSISTANT_ENV_VARIABLE,
    LLM_ASSISTANT_CONFIGURATION_FILENAME,
)

from collections import namedtuple
from git.exc import InvalidGitRepositoryError
import git
from pathlib import Path
import pytest
import tempfile
from typing import Optional


def create_prompt_config_file(config_file: Path):
    minimum_config = f"""
    user_prompt=""
    system_prompt=""
    """

    with open(config_file, "w") as f:
        f.write(minimum_config)


def create_llm_assistant_config_file(config_file: Path, prompts_dir: Path):
    minimum_config = f"""
    [prompt]
    git_user=""
    local_folder="{str(prompts_dir)}"
    versioning = ""
    """

    with open(config_file, "w") as f:
        f.write(minimum_config)


def test_fail_if_config_not_present():
    with tempfile.TemporaryDirectory() as dir:
        p_dir = Path(dir)
        assert api.is_prompt_repository(p_dir) is False


def test_fail_if_missing_mandatory_keys():
    with tempfile.TemporaryDirectory() as dir:
        p_dir = Path(dir)
        config = p_dir / "config.toml"
        config.touch()
        assert api.is_prompt_repository(p_dir) is False


def test_is_prompt_repository():
    with tempfile.TemporaryDirectory() as dir:
        p_dir = Path(dir)
        config = p_dir / "config.toml"

        create_prompt_config_file(config)
        assert api.is_prompt_repository(p_dir) is True


def minimum_config(fn):
    def inner(*args, **kwargs):
        with tempfile.TemporaryDirectory() as dir:
            p_dir = Path(dir)
            config = p_dir / f"{LLM_ASSISTANT_CONFIGURATION_FILENAME}"

            prompts_dir = p_dir / "prompts"
            prompts_dir.mkdir()

            create_llm_assistant_config_file(config, prompts_dir)

            fn(*args, config_dir=p_dir, prompts_dir=prompts_dir, **kwargs)

    return inner


def repository_config(fn):
    def inner(*args, **kwargs):
        with tempfile.TemporaryDirectory() as dir:
            p_dir = Path(dir)
            config = p_dir / f"{LLM_ASSISTANT_CONFIGURATION_FILENAME}"

            prompts_dir = p_dir / "prompts"
            prompts_dir.mkdir()

            create_llm_assistant_config_file(config, prompts_dir)

            mock_prompts = ["correct-text", "translate"]
            for mp in mock_prompts:
                p_dir = prompts_dir / mp
                p_dir.mkdir()

                create_prompt_config_file(p_dir / "config.toml")
                git.Repo.init(p_dir)

            fn(*args, config_dir=p_dir, prompts_dir=prompts_dir, **kwargs)

    return inner


def test_non_existing_prompt_folder(monkeypatch):
    @minimum_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False

        if not prompts_dir:
            assert False

        monkeypatch.chdir(config_dir)

        with pytest.raises(FileNotFoundError):
            api.get_tracked_prompt("correct-text")

    inner()


def test_not_valid_repository(monkeypatch):
    @minimum_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False

        if not prompts_dir:
            assert False

        monkeypatch.chdir(config_dir)
        correct_text_prompt = prompts_dir / "correct-text"
        correct_text_prompt.mkdir()

        with pytest.raises(InvalidGitRepositoryError):
            api.get_tracked_prompt("correct-text")

    inner()


def test_get_tracked_prompts(monkeypatch):
    @repository_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False

        if not prompts_dir:
            assert False

        monkeypatch.chdir(config_dir)

        l_tp = list(api.get_tracked_prompts())
        names = [tp.name for tp in l_tp]
        assert "correct-text" in names
        assert "translate" in names

    inner()


def test_get_prompt_versions(monkeypatch):
    @repository_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False

        if not prompts_dir:
            assert False

        monkeypatch.chdir(config_dir)
        monkeypatch.setattr(
            utils,
            "get_versions",
            lambda x: ["2.0.1", "2.0.0", "3.0.0", "2.1.3", "1.0.0"],
        )
        versions = api.get_prompt_versions(prompts_dir / "correct-text")

        assert ["1.0.0", "2.0.0", "2.0.1", "2.1.3", "3.0.0"] == versions

    inner()


def test_get_most_recent_version_before_commit(monkeypatch):
    @repository_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False

        if not prompts_dir:
            assert False

        Tag = namedtuple("Tag", "name")
        monkeypatch.chdir(config_dir)
        monkeypatch.setattr(
            utils,
            "get_most_recent_tags_before_commit",
            lambda x, y: [
                Tag("v2.0.1"),
                Tag("v2.0.0"),
                Tag("v3.0.0"),
                Tag("v2.1.3"),
                Tag("v1.0.0"),
            ],
        )

        version = api.get_most_recent_version_before_commit(
            prompts_dir / "correct-text", "commit"
        )
        assert version == "2.0.1"

    inner()


def test_no_version_registered(monkeypatch):
    @repository_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False

        if not prompts_dir:
            assert False

        monkeypatch.chdir(config_dir)

        monkeypatch.setattr(git.Repo, "commit", lambda x: "")
        monkeypatch.setattr(
            utils, "get_most_recent_tags_before_commit", lambda x, y: []
        )
        monkeypatch.setattr(utils, "get_commit_tags", lambda x, y: [])

        version = api.get_current_version(prompts_dir / "correct-text")
        assert version is None

    inner()


def test_current_version(monkeypatch):
    @repository_config
    def inner(config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        if not config_dir:
            assert False
        if not prompts_dir:
            assert False

        Tag = namedtuple("Tag", "name")

        monkeypatch.chdir(config_dir)

        monkeypatch.setattr(git.Repo, "commit", lambda x: "")
        monkeypatch.setattr(
            utils, "get_most_recent_tags_before_commit", lambda x, y: [Tag("v2.0.1")]
        )
        monkeypatch.setattr(utils, "get_commit_tags", lambda x, y: [])

        version = api.get_current_version(prompts_dir / "correct-text")
        assert version == "2.0.1"

    inner()


def test_suggest_next_version(monkeypatch):
    monkeypatch.setattr(api, "get_prompt_versions", lambda x: [])
    nv = api.suggest_next_version("", "1.0.0", model.ChangeNature.PromptTweak)
    assert nv == "1.0.0"

    monkeypatch.setattr(api, "get_prompt_versions", lambda x: ["1.0.0"])
    nv = api.suggest_next_version("", "1.0.0", model.ChangeNature.PromptTweak)
    assert nv == "1.0.1"

    monkeypatch.setattr(api, "get_prompt_versions", lambda x: ["1.0.0"])
    nv = api.suggest_next_version("", "1.0.0", model.ChangeNature.InterfaceUpdate)
    assert nv == "1.1.0"

    monkeypatch.setattr(api, "get_prompt_versions", lambda x: ["1.0.0"])
    nv = api.suggest_next_version("", "1.0.0", model.ChangeNature.ScopeChange)
    assert nv == "2.0.0"

    monkeypatch.setattr(api, "get_prompt_versions", lambda x: ["1.0.0", "2.0.0"])
    nv = api.suggest_next_version("", "1.0.0", model.ChangeNature.ScopeChange)
    assert nv == "3.0.0"


def test_sync():
    pass


def test_update_change_log():
    s = """# V1

## 1.0.0

Contents of v1.0.0

## 1.1.0

Contents of v1.1.0

# V2

## 2.0.0

Contents of v2.0.0

## 2.0.1

Contents of v2.0.1

## 1.1.1

Contents of v1.1.1
"""

    expected_str = """# V1

## 1.0.0

Contents of v1.0.0



## 1.1.0

Contents of v1.1.0



## 1.1.1

Contents of v1.1.1

# V2

## 2.0.0

Contents of v2.0.0



## 2.0.1

Contents of v2.0.1



"""
    result = api.update_changelog(s)
    print(result)
    assert result == expected_str
