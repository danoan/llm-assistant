from danoan.llm_assistant.prompt.core import api
from danoan.llm_assistant.prompt.cli import utils as cli_utils

from typing import List


def __list_prompts__() -> List[str]:
    entries = []
    for tp in api.get_tracked_prompts():
        entry = f"{tp.name}: @{tp.current_tag}"
        entries.append(entry)
    return entries


def list_prompts():
    cli_utils.ensure_prompt_collection_folder_exists()
    cli_utils.print_panel_list("Tracked Prompts", __list_prompts__())
