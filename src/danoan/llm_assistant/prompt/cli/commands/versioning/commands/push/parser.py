from danoan.llm_assistant.prompt.core import api, model, utils
from danoan.llm_assistant.prompt.cli import utils as cli_utils

import argparse
from collections import deque
import git
from typing import Optional


def __get_most_recent_version_before_commit__(
    repository_folder: str, commit_hash: str
) -> Optional[str]:
    tags = utils.get_most_recent_tags_before_commit(repository_folder, commit_hash)
    for t in tags:
        if t.name[0] != "v":
            continue

        return t.name[1:]
    return None


def ask_to_version(tracked_prompt: model.TrackedPrompt) -> bool:
    ans = input(
        f"The prompt {tracked_prompt.name} is not versioned. A version is necessary to continue. Do you like to version it? (y,n): "
    )
    if ans.lower() == "y":
        return True
    else:
        return False

    return True


def ask_for_a_version(tracked_prompt: model.TrackedPrompt) -> bool:
    repo = git.Repo(tracked_prompt.repository_path)
    current_tags = utils.get_commit_tags(tracked_prompt.repository_path, repo.commit())
    no_version_at_all = (
        len(
            utils.get_most_recent_tags_before_commit(
                tracked_prompt.repository_path, repo.commit()
            )
        )
        == 0
    )
    current_commit_is_not_versioned = len(current_tags) == 0 and not no_version_at_all
    proposed_versions = ["v1.0.0"]

    if current_commit_is_not_versioned:
        most_recent_version = __get_most_recent_version_before_commit__(
            tracked_prompt.repository_path, repo.commit()
        )
        if not most_recent_version:
            print("No commit found")
            exit(1)
        variation, major, minor = [int(x) for x in most_recent_version.split(".")]
        bump_variation = f"{variation+1}.{major}.{minor}"
        bump_major = f"{variation}.{major+1}.{minor}"
        bump_minor = f"{variation}.{major}.{minor+1}"
        proposed_versions = [f"v{bump_variation}", f"v{bump_major}", f"v{bump_minor}"]

    cli_utils.print_previous_commit(tracked_prompt.repository_path, repo.commit())
    ans = input(
        f"Which version would you like to set? (Proposed versions are {proposed_versions}): "
    )
    version = proposed_versions[0]
    if len(ans.strip()) != 0:
        version = ans
    utils.push_new_version(tracked_prompt.repository_path, version)

    return True


def __push__(repository_name: str, version: Optional[str] = None, *args, **kwargs):
    """
    Push a new prompt version.

    The version of a prompt is made of three components.
        prompt_id.major.minor

    The prompt_id identifies a prompt variation. For example,
    we may have a prompt to correct text in some language. The
    1.x.x series could be dedicated to very simplistic versions
    of these prompts that only return the corrected version. The
    2.x.x series could be dedicated to versions in which besides
    the correction, the prompt also gives the explanation and
    so on.

    We bump minor every time one of the following situations:
        - Add more examples
        - Any edition on user and system prompts that do
          not modify the input neither output structure.
    We bump the major every time we do one of the following:
        - Update input or output structure.
    """
    cli_utils.ensure_configuration_file_exists()
    cli_utils.ensure_prompt_repository_exists(repository_name)

    tp = api.get_tracked_prompt(repository_name)

    repo = git.Repo(tp.repository_path)
    if repo.is_dirty():
        print("There are uncommited changes on the index.")
        cli_utils.print_staging_area(tp.repository_path)
        exit(1)

    current_tags = utils.get_commit_tags(tp.repository_path, repo.commit())
    if len(current_tags) == 0:
        cli_utils.print_commits(
            tp.repository_path, utils.get_non_versioned_commits(tp.repository_path)
        )
        prompts_queue = deque([ask_to_version, ask_for_a_version])
        while len(prompts_queue) > 0:
            prompt = prompts_queue.popleft()
            if not prompt(tp):
                exit(1)
    else:
        print("The latest changes are already versioned")
        cli_utils.print_commits(tp.repository_path, [repo.commit()])


def extend_parser(subparser_action=None):
    command_name = "push"
    description = __push__.__doc__
    help = description.split(".")[0] if description else ""

    if subparser_action:
        parser = subparser_action.add_parser(
            command_name,
            help=help,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    else:
        parser = argparse.ArgumentParser(
            command_name,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    parser.add_argument("repository_name", type=str)
    parser.add_argument("--version", type=str)

    parser.set_defaults(func=__push__, subcommand_help=parser.print_help)

    return parser
