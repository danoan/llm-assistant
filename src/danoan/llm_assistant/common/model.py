from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class PromptRepositoryConfiguration:
    git_user: str
    local_folder: Path
    versioning: Dict[str, str]

    def __post_init__(self):
        self.local_folder = Path(self.local_folder)

    def __asdict__(self) -> Dict[str, str]:
        d = asdict(self)
        d["local_folder"] = str(self.local_folder)

        return d

    def __str__(self):
        return (
            f"git_user: {self.git_user}\n"
            f"local_folder: {self.local_folder}\n"
            f"versioning: {self.local_folder}\n"
        )


@dataclass
class RunnerConfiguration:
    openai_key: Optional[str] = None
    model: Optional[str] = None
    use_cache: bool = False
    cache_path: Optional[Path] = None
    local_folder: Optional[Path] = None

    def __post_init__(self):
        self.cache_path = Path(self.cache_path) if self.cache_path else None
        self.local_folder = Path(self.local_folder) if self.local_folder else None

    def __asdict__(self):
        d = asdict(self)
        if self.cache_path:
            d["cache_path"] = str(self.cache_path)
        if self.local_folder:
            d["local_folder"] = str(self.local_folder)

        return d

    def __str__(self):
        return (
            f"openai_key: <<HIDDEN>>\n"
            f"model: {self.model}\n"
            f"use_cache: {self.use_cache}\n"
            f"cache_path: {self.cache_path}\n"
            f"local_folder: {self.local_folder}\n"
        )


@dataclass
class LLMAssistantConfiguration:
    runner: Union[Optional[RunnerConfiguration], Dict[str, Any]] = None
    prompt: Union[Optional[PromptRepositoryConfiguration], Dict[str, Any]] = None

    def __post_init__(self):
        if type(self.runner) is dict:
            self.runner = RunnerConfiguration(**self.runner)

        if type(self.prompt) is dict:
            self.prompt = PromptRepositoryConfiguration(**self.prompt)

    def __str__(self):
        return (
            f"Runner configuration\n\n{self.runner}\n\n"
            f"Prompt repository configuration\n\n{self.prompt}"
        )

    def __asdict__(self):
        return {
            "runner": self.runner.__asdict__()
            if type(self.runner) is RunnerConfiguration
            else self.runner,
            "prompt": self.prompt.__asdict__()
            if type(self.prompt) is PromptRepositoryConfiguration
            else self.prompt,
        }


@dataclass
class PromptConfiguration:
    name: str
    system_prompt: str
    user_prompt: str
    model: Optional[str] = None
