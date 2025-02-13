from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.common.model import PromptConfiguration, RunnerConfiguration
from danoan.llm_assistant.common import config
from danoan.llm_assistant.common import utils

from danoan.llm_assistant.prompt.cli import utils as cli_utils
from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.runner.core import api as llma

import git
import json
import logging
import sys
import toml
from tempfile import TemporaryDirectory

setup_logging()
logger = logging.getLogger(__name__)


def __load_prompt_configuration_version__(
    prompt_name: str, version: str
) -> PromptConfiguration:
    tp = api.get_tracked_prompt(prompt_name)
    repo = git.Repo(tp.repository_path)

    if version == "current":
        config_toml = repo.git.show(f"HEAD:config.toml")
    else:
        repo.git.checkout(version)
        config_toml = repo.git.show(f"{version}:config.toml")

    return PromptConfiguration(**toml.loads(config_toml))


def __run_tests__(
    runner_configuration: RunnerConfiguration,
    prompt_name: str,
    base_version: str,
    compare_version: str,
):
    base_prompt_config = __load_prompt_configuration_version__(
        prompt_name, base_version
    )
    compare_prompt_config = __load_prompt_configuration_version__(
        prompt_name, compare_version
    )

    test_model = api.get_prompt_test_regression_filepath(prompt_name)
    test_run = test_model.parent / runner_configuration.model / test_model.name

    with open(test_run, "r") as fi:
        input_obj = json.load(fi)

        for entry in input_obj:
            base_response = llma.custom(base_prompt_config, **entry["input"])
            compare_response = llma.custom(compare_prompt_config, **entry["input"])

            try:
                base_response_obj = json.loads(base_response.content)
            except:
                base_response_obj = base_response.content

            try:
                compare_response_obj = json.loads(compare_response.content)
            except:
                compare_response_obj = compare_response.content

            base_response_str = json.dumps(
                base_response_obj, ensure_ascii=False, indent=2
            )
            compare_response_str = json.dumps(
                compare_response_obj, ensure_ascii=False, indent=2
            )

            yield (base_response_str, compare_response_str)


def run_tests(
    prompt_name: str, use_cache: bool, base_version: str, compare_version: str
):
    runner_configuration = config.get_configuration().runner
    runner_configuration.use_cache = use_cache
    llma.LLMAssistant().setup(
        utils.generate_absolute_runner_config(runner_configuration)
    )

    try:
        for base_response_str, compare_response_str in __run_tests__(
            runner_configuration, prompt_name, base_version, compare_version
        ):
            cli_utils.print_side_by_side(
                base_response_str,
                compare_response_str,
                left_title="Base",
                right_title="Compare",
            )
    except FileNotFoundError as ex:
        print(ex)
        exit(1)
