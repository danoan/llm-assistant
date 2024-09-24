from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Configuration:
    local_repository_folder: str
    openai_key: Optional[str] = None
    prompt_repositories: Optional[List[str]] = None


@dataclass
class TrackedPrompt:
    name: str
    repository_path: Path
    current_tag: str
    branches: List[str]
