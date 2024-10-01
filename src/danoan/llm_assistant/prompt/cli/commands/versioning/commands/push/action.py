from danoan.llm_assistant.prompt.core import api, model, utils
from danoan.llm_assistant.prompt.cli import utils as cli_utils

import git
from pathlib import Path
from typing import List, Optional


def __get_most_recent_version_before_commit__(
    repository_folder: str, commit_hash: str
) -> Optional[str]:
    tags = utils.get_most_recent_tags_before_commit(repository_folder, commit_hash)
    for t in tags:
        if t.name[0] != "v":
            continue

        return t.name[1:]
    return None


def __propose_new_version_from_current_one__(current_version: str) -> List[str]:
    variation, major, minor = [int(x) for x in current_version.split(".")]
    bump_variation = f"{variation+1}.{major}.{minor}"
    bump_major = f"{variation}.{major+1}.{minor}"
    bump_minor = f"{variation}.{major}.{minor+1}"
    return [f"v{bump_variation}", f"v{bump_major}", f"v{bump_minor}"]


def __get_current_version__(repository_folder: Path) -> Optional[str]:
    repo = git.Repo(repository_folder)
    current_tags = utils.get_commit_tags(repository_folder, repo.commit())

    no_version_at_all = (
        len(utils.get_most_recent_tags_before_commit(repository_folder, repo.commit()))
        == 0
    )

    if no_version_at_all:
        return None

    current_commit_is_not_versioned = len(current_tags) == 0 and not no_version_at_all
    most_recent_version = None
    if current_commit_is_not_versioned:
        most_recent_version = __get_most_recent_version_before_commit__(
            repository_folder, repo.commit()
        )
    else:
        most_recent_version = current_tags[0]

    return most_recent_version


def __ask_to_version__(tracked_prompt: model.TrackedPrompt) -> bool:
    ans = input(
        f"The prompt {tracked_prompt.name} is not versioned. A version is necessary to continue. Do you like to version it? (y,n): "
    )
    if ans.lower() == "y":
        return True
    else:
        return False

    return True


def __ask_for_a_version__(tracked_prompt: model.TrackedPrompt) -> bool:
    current_version = __get_current_version__(tracked_prompt.repository_path)
    if not current_version:
        current_version = "v0.0.0"
    proposed_versions = __propose_new_version_from_current_one__(current_version)

    repo = git.Repo(tracked_prompt.repository_path)
    cli_utils.print_previous_commit(tracked_prompt.repository_path, repo.commit())
    ans = input(
        f"Which version would you like to set? (Proposed versions are {proposed_versions}): "
    )
    version = proposed_versions[0]
    if len(ans.strip()) != 0:
        version = ans
    utils.push_new_version(tracked_prompt.repository_path, version)

    return True


def push(prompt_name: str, version: Optional[str] = None, *args, **kwargs):
    cli_utils.ensure_configuration_file_exists()
    cli_utils.ensure_prompt_repository_exists(prompt_name)

    tp = api.get_tracked_prompt(prompt_name)

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

        if not __ask_to_version__(tp):
            exit(1)

        if not __ask_for_a_version__(tp):
            exit(1)
    else:
        print("The latest changes are already versioned")
        cli_utils.print_commits(tp.repository_path, [repo.commit()])
