from danoan.llm_assistant.common.logging_config import setup_logging
from danoan.llm_assistant.prompt.core import api, model, utils
from danoan.llm_assistant.prompt.cli import utils as cli_utils

import git
import logging
from pathlib import Path
import subprocess
from typing import Callable, List, Optional, Tuple

setup_logging()
logger = logging.getLogger(__name__)

###################################
# Lazy Actions
###################################


def action(fn):
    def wrapper(*args, **kwargs):
        def inner():
            return fn(*args, **kwargs)

        return inner

    return wrapper


@action
def checkout_existing_branch(repository_path: Path, branch_name: str):
    repo = git.Repo(repository_path)
    logger.info(f"Checkout existing branch: {branch_name}")
    repo.git.checkout(branch_name)


@action
def checkout_new_branch(repository_path: Path, branch_name: str):
    repo = git.Repo(repository_path)
    logger.info(f"Creating branch: {branch_name}")
    repo.git.checkout(b=branch_name)


@action
def interactive_add(repository_path: Path):
    subprocess.run(
        [
            "git",
            "add",
            "-i",
        ],
        cwd=repository_path,
    )


@action
def add_file(repository_path: Path, filename: str):
    repo = git.Repo(repository_path)
    repo.git.add(filename)


@action
def commit_message(repository_path: Path, message: str):
    repo = git.Repo(repository_path)
    logger.info(f"Commiting changes: {message}")
    repo.git.commit(m=f"{message}")


@action
def push_branch(repository_path: Path):
    repo = git.Repo(repository_path)
    logger.info(f"Pushing branch: {repo.active_branch}")
    repo.remote().push(repo.active_branch)


@action
def push_tag(repository_path: Path, tag_name: str, message: str):
    repo = git.Repo(repository_path)
    tag_name = f"v{tag_name}"
    logger.info(f"Creating tag: {tag_name}")
    tag = repo.create_tag(tag_name, repo.commit(), message=message)
    repo.remote().push(tag)


@action
def stash_save(repository_path: Path):
    repo = git.Repo(repository_path)
    repo.git.stash("save", "current changes")


@action
def stash_pop(repository_path: Path):
    repo = git.Repo(repository_path)
    repo.git.stash("pop")


@action
def rewrite_readme_file(
    tp: model.TrackedPrompt, version: model.PromptVersion, changes_description: str
):
    readme_file = tp.repository_path / "README.md"

    with open(readme_file) as f:
        readme = f.read()

    readme += f"\n## {version}\n\n{changes_description}\n"
    rewriten_readme = api.update_changelog(readme)

    with open(readme_file, "w") as f:
        f.write(rewriten_readme)


###################################
# Helpers
###################################


def __fetch_remote_data__(tp: model.TrackedPrompt):
    repo = git.Repo(tp.repository_path)
    logger.info("Fetching repository data")
    repo.remote().fetch(tags=True)


def __describe_changes__(tp: model.TrackedPrompt) -> str:
    logger.info("Describe the changes (finish the input by outputing a line with $$)")
    description = ""
    v = input()
    while v != "$$":
        description += f"{v}\n"
        v = input()
    return description


def __update_changelog__(
    tp: model.TrackedPrompt,
    changes_description: str,
    version: model.PromptVersion,
    branch_name: str,
) -> List[Callable[[], None]]:
    git_commands = [
        checkout_existing_branch(tp.repository_path, branch_name),
        rewrite_readme_file(tp, version, changes_description),
        add_file(tp.repository_path, "README.md"),
        commit_message(tp.repository_path, message=f"Update changelog: Add {version}"),
        push_branch(tp.repository_path),
    ]

    return git_commands


def __classify_changes__() -> model.ChangeNature:
    options = [
        "Prompt tweak: Add extra examples, edit intructions to be more precise about some aspect or remove ambiguity.",
        "Interface update: The expected input values or the output format has changed.",
        "Scope change: The prompt become more specialized or more general.",
    ]

    cli_utils.print_vertical_panel_list("Nature of changes", options)
    item_number = input("\nWhat is the nature of the changes? ")
    if item_number == "1":
        return model.ChangeNature.PromptTweak
    elif item_number == "2":
        return model.ChangeNature.InterfaceUpdate
    elif item_number == "3":
        return model.ChangeNature.ScopeChange
    else:
        raise RuntimeError("Invalid option")


def __suggest_version__(tp: model.TrackedPrompt) -> Tuple[str, model.ChangeNature]:
    current_version = api.get_current_version(tp.repository_path)
    if not current_version:
        current_version = "0.0.0"

    sorted_tags = api.get_prompt_versions(tp.repository_path)

    cli_utils.print_panel_list("Current versions", sorted_tags)
    s = input(f"Enter a base version ({current_version}): ")
    if s.strip() != "":
        current_version = s

    cn = __classify_changes__()
    suggested_version = api.suggest_next_version(
        tp.repository_path, current_version, cn
    )

    while True:
        sv_str = input(f"Suggested version ({suggested_version}): ")
        if sv_str.strip() != "":
            suggested_version = model.PromptVersion(sv_str, cn)

        if suggested_version in set(sorted_tags):
            logger.info(
                f"Version {suggested_version} exists already. Please choose another one"
            )
        else:
            break

    return suggested_version, cn


def __commit_changes__(
    tp: model.TrackedPrompt,
    changes_nature: model.ChangeNature,
    changes_description: str,
    version: model.PromptVersion,
) -> List[Callable[[], None]]:
    git_commands = []

    branch_name = f"v{version.major}.{version.minor}"
    repo = git.Repo(tp.repository_path)
    current_branch = repo.active_branch.name
    if current_branch != branch_name:
        logger.error(
            f"You should first move to branch {branch_name} and resolve all eventual conflicts before continue."
        )
        exit(1)

    # Start git add interactive
    git_commands.append(interactive_add(tp.repository_path))

    # Update changelog

    git_commands.extend(
        [
            rewrite_readme_file(tp, version, changes_description),
            add_file(tp.repository_path, "README.md"),
        ]
    )

    # Commit the changes
    message = f"Release version {version}"
    git_commands.append(commit_message(tp.repository_path, message))

    return git_commands


def __create_tag__(
    tp: model.TrackedPrompt,
    changes_nature: model.ChangeNature,
    changes_description: str,
    version: model.PromptVersion,
) -> List[Callable[[], None]]:
    git_commands = []

    branch_name = f"v{version.major}.{version.minor}"
    git_commands.append(checkout_existing_branch(tp.repository_path, branch_name))

    git_commands.append(push_branch(tp.repository_path))

    message = f"Release version {version}\n\n{changes_description}"
    git_commands.append(push_tag(tp.repository_path, str(version), message))
    return git_commands


###################################
# Main
###################################


def push(prompt_name: str, version: Optional[str] = None, *args, **kwargs):
    cli_utils.ensure_configuration_file_exists()
    cli_utils.ensure_prompt_repository_exists(prompt_name)

    tp = api.get_tracked_prompt(prompt_name)
    __fetch_remote_data__(tp)

    changes_description = __describe_changes__(tp)
    suggested_version, changes_nature = __suggest_version__(tp)

    pv = model.PromptVersion(suggested_version)

    git_commands = []
    git_commands.extend(__commit_changes__(tp, changes_nature, changes_description, pv))
    git_commands.extend(__update_changelog__(tp, changes_description, pv, "master"))
    git_commands.extend(__create_tag__(tp, changes_nature, changes_description, pv))

    for command in git_commands:
        command()
