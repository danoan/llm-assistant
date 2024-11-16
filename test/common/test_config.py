import os
import tempfile
from pathlib import Path

import pytest

from danoan.llm_assistant.common import config, exception


def test_get_configuration_folder_cwd(monkeypatch):
    # Configuration file in the current working dir
    with tempfile.TemporaryDirectory() as _tmpdir:
        tmpdir = Path(_tmpdir)
        config_file = tmpdir / config.LLM_ASSISTANT_CONFIGURATION_FILENAME
        config_file.touch()

        monkeypatch.chdir(tmpdir)
        assert config.get_configuration_folder() == tmpdir


def test_get_configuration_folder_parent_cwd(monkeypatch):
    # Configuration file in a parent directory of current working dir
    with tempfile.TemporaryDirectory() as _tmpdir:
        tmpdir = Path(_tmpdir)
        config_file = tmpdir / config.LLM_ASSISTANT_CONFIGURATION_FILENAME
        config_file.touch()

        working_dir = tmpdir / "A" / "B" / "C"
        working_dir.mkdir(parents=True)

        monkeypatch.chdir(working_dir)
        assert config.get_configuration_folder() == tmpdir


def test_get_configuration_folder_envvar(monkeypatch):
    # Configuration file defined by environment variable
    with tempfile.TemporaryDirectory() as _envvar_dir:
        envvar_dir = Path(_envvar_dir)
        monkeypatch.setenv(config.LLM_ASSISTANT_ENV_VARIABLE, str(envvar_dir))

        assert config.get_configuration_folder() == envvar_dir


def test_get_configuration_folder_error():
    # No configuration file and not environment variable defined
    with pytest.raises(exception.EnvironmentVariableNotDefinedError) as ex:
        config.get_configuration_folder()


def test_get_configuration_filepath(monkeypatch):
    monkeypatch.setenv(config.LLM_ASSISTANT_ENV_VARIABLE, os.getcwd())
    assert (
        config.get_configuration_filepath()
        == Path(os.getcwd()) / config.LLM_ASSISTANT_CONFIGURATION_FILENAME
    )


def test_get_configuration(monkeypatch):
    config_file_toml = """
    [runner]
    openai_key = "key"
    model = "gpt-3.5-turbo"
    use_cache = true
    cache_path = "cache.db"
    """
    with tempfile.TemporaryDirectory() as _tmpdir:
        tmpdir = Path(_tmpdir)
        config_file = tmpdir / config.LLM_ASSISTANT_CONFIGURATION_FILENAME
        with open(config_file, "w") as f:
            f.write(config_file_toml)

        monkeypatch.chdir(tmpdir)
        config_obj = config.get_configuration()
        assert config_obj.runner.openai_key == "key"
        assert config_obj.runner.model == "gpt-3.5-turbo"
        assert config_obj.runner.use_cache == True


def test_get_configuration_error(monkeypatch):
    with tempfile.TemporaryDirectory() as _tmpdir:
        tmpdir = Path(_tmpdir)
        monkeypatch.chdir(tmpdir)
        with pytest.raises(exception.EnvironmentVariableNotDefinedError):
            config.get_configuration()

        monkeypatch.setenv(str(config.LLM_ASSISTANT_ENV_VARIABLE), str(tmpdir))
        with pytest.raises(exception.ConfigurationFileDoesNotExistError):
            config.get_configuration()


def test_get_prompt_configuration(monkeypatch):
    config_file_toml = """
    [runner]
    openai_key = "key"
    model = "gpt-3.5-turbo"
    use_cache = true
    cache_path = "cache.db"

    [prompt]
    git_user = "danoan"
    prompt_collection_folder = "prompts"
    """

    prompt_config_file_toml = """
    name = ""
    system_prompt = ""
    user_prompt = ""
    """

    with tempfile.TemporaryDirectory() as _tmpdir:
        tmpdir = Path(_tmpdir)

        prompt_folder = tmpdir / "prompts" / "correct-text"
        prompt_folder.mkdir(parents=True)
        prompt_config_file = prompt_folder / "config.toml"
        with open(prompt_config_file, "w") as f:
            f.write(prompt_config_file_toml)

        config_file = tmpdir / config.LLM_ASSISTANT_CONFIGURATION_FILENAME
        with open(config_file, "w") as f:
            f.write(config_file_toml)

        monkeypatch.chdir(tmpdir)
        assert config.get_prompt_configuration("correct-text") is not None
