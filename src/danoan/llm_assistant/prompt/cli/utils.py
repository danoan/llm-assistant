from pathlib import Path
from typing import Any, List

from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from danoan.llm_assistant.common import config
from danoan.llm_assistant.prompt.core import api, utils

###################################
# GUI Primitives
###################################


_console = Console()


def _make_numbered_list(entries: List[Any], padding=(0, 10), **kwargs) -> Columns:
    list_elements = [f"{i}. {s}" for i, s in enumerate(entries, 1)]
    return Columns(list_elements, padding=padding, **kwargs)


def _make_numbered_vertical_list(entries: List[Any]) -> Text:
    text = Text()
    for i, e in enumerate(entries, 1):
        text.append(f"{i}. {e}")
        if i != len(entries):
            text.append("\n")
    return text


def print_list(*args, **kwargs):
    _console.print(_make_numbered_list(*args, **kwargs))


def print_vertical_list(entries: List[Any]):
    _console.print(_make_numbered_vertical_list(entries))


def print_panel_list(title, entries: List[Any], **kwargs):
    columns = _make_numbered_list(entries)
    panel = Panel(columns, title=title, **kwargs)
    _console.print(panel)


def print_vertical_panel_list(title, entries: List[Any], **kwargs):
    panel = Panel(_make_numbered_vertical_list(entries), title=title)
    _console.print(panel)


def print_panel_table(title, rows, **kwargs):
    table = Columns(rows, column_first=True)
    panel = Panel(table, title=title, **kwargs)
    _console.print(panel)


###################################
# GUI Common Derivatives
###################################


def print_commits(repository_folder: Path, commits_hashes: List[str]):
    """
    Print a summary of the given commit hashes.

    <Hash> <title> <tags>
    """
    rows = []
    for commit_hash in commits_hashes:
        commit = utils.get_commit(repository_folder, commit_hash)
        sha = Text(commit.hexsha)
        title = Text(commit.message.splitlines()[0])
        tags = ",".join(
            [t.name for t in utils.get_commit_tags(repository_folder, commit_hash)]
        )
        list_tags = Text(f"({tags})")
        rows.append(Columns([sha, title, list_tags]))
    print_panel_table("Previous Commits", rows)


def print_previous_commit(repository_folder: Path, commit_hash: str):
    """
    Print a summary of all commits previous the given one.
    """
    most_recent_tags = utils.get_most_recent_tags_before_commit(
        repository_folder, commit_hash
    )
    if len(most_recent_tags) == 0:
        return
    tag = most_recent_tags[-1]
    hashes = utils.get_all_commits_in_between(
        repository_folder, commit_hash, tag.commit
    )
    print_commits(repository_folder, hashes)


def print_staging_area(repository_folder: Path):
    """
    Print respoitory staging area.
    """
    row = []
    for i, entry in enumerate(utils.get_staging_area(repository_folder), 1):
        row.append(Columns([str(i), entry.a_path, entry.change_type]))

    print_panel_table("Staging Area", row)


def print_side_by_side(
    left_content, right_content, left_title="Left", right_title="Right"
):
    console = Console()

    terminal_width = console.size.width
    column_width = terminal_width // 2 - 1

    row = [
        Panel(left_content, style="orange1", title=left_title, width=column_width),
        Panel(right_content, style="pink3", title=right_title, width=column_width),
    ]

    c = Columns(row, equal=True, expand=True)
    print(c)


###################################
# Configuration file
###################################


def ensure_configuration_file_exists():
    if not config.get_configuration_filepath().exists():
        print(
            f"Configuration file for prompt-evaluator does not exist. It should be located \
            at {config.get_configuration_filepath()}"
        )
        exit(1)


def ensure_prompt_repository_exists(repository_name: str):
    repository_folder = api.get_prompts_folder() / repository_name

    if not api.is_prompt_repository(repository_folder):
        print(f"The path {repository_folder} does not point to a prompt repository.")
        exit(1)
