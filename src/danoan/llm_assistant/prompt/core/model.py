from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class TrackedPrompt:
    name: str
    repository_path: Path
    current_tag: str
    branches: List[str]
