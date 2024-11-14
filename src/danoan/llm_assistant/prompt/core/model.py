from dataclasses import dataclass
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import List


@dataclass
class TrackedPrompt:
    name: str
    repository_path: Path
    current_tag: str
    branches: List[str]


class ChangeNature(Enum):
    PromptTweak = 1
    InterfaceUpdate = 2
    ScopeChange = 3


@total_ordering
class PromptVersion:
    class IncrementerType(Enum):
        Major = 1
        Minor = 2
        Fix = 3

    def __init__(
        self, version: str, incrementer_type: IncrementerType = IncrementerType.Major
    ):
        self.incrementer_type = incrementer_type
        self.major, self.minor, self.fix = [int(x) for x in version.split(".")]

    def __version_id__(self) -> int:
        v = int(self.major) * 1e5 + int(self.minor) * 1e4 + int(self.fix) * 1e3
        return int(v)

    def __add__(self, x: int):
        if self.incrementer_type == PromptVersion.IncrementerType.Major:
            self.major += 1
        elif self.incrementer_type == PromptVersion.IncrementerType.Minor:
            self.minor += 1
        elif self.incrementer_type == PromptVersion.IncrementerType.Fix:
            self.fix += 1

        return self

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.fix}"

    def __lt__(self, other):
        if not isinstance(other, PromptVersion):
            raise NotImplemented
        return self.__version_id__() < other.__version_id__()

    def __eq__(self, other):
        if not isinstance(other, PromptVersion):
            raise NotImplemented
        return self.__version_id__() == other.__version_id__()

    def __hash__(self):
        return hash((self.major, self.minor, self.fix))

    def set_incrementer(self, incremeter_type: IncrementerType):
        self.incrementer_type = incremeter_type
