"""
Data models shared by prompt and runner modules.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

#################################
# Configuration data
#################################


@dataclass
class PromptRepositoryConfiguration:
    git_user: str
    prompt_collection_folder: Path
    versioning: Optional[Dict[str, str]] = None

    def __post_init__(self):
        self.prompt_collection_folder = Path(self.prompt_collection_folder)

    def __asdict__(self) -> Dict[str, str]:
        d = asdict(self)
        d["prompt_collection_folder"] = str(self.prompt_collection_folder)

        return d

    def __str__(self):
        return (
            f"git_user: {self.git_user}\n"
            f"prompt_collection_folder: {str(self.prompt_collection_folder)}\n"
            f"versioning: {self.versioning}\n"
        )


@dataclass
class RunnerConfiguration:
    openai_key: Optional[str] = None
    model: Optional[str] = None
    use_cache: bool = False
    cache_path: Optional[Path] = None

    def __post_init__(self):
        self.cache_path = Path(self.cache_path) if self.cache_path else None

    def __asdict__(self):
        d = asdict(self)
        if self.cache_path:
            d["cache_path"] = str(self.cache_path)

        return d

    def __str__(self):
        return (
            f"openai_key: <<HIDDEN>>\n"
            f"model: {self.model}\n"
            f"use_cache: {self.use_cache}\n"
            f"cache_path: {str(self.cache_path)}\n"
        )


@dataclass
class LLMAssistantConfiguration:
    runner: Optional[RunnerConfiguration] = None
    prompt: Optional[PromptRepositoryConfiguration] = None

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

    @classmethod
    def from_dict(
        cls,
        runner: Optional[Dict[str, Any]] = None,
        prompt: Optional[Dict[str, Any]] = None,
    ):
        inst_runner = None
        inst_prompt = None
        if runner:
            inst_runner = RunnerConfiguration(**runner)
        if prompt:
            inst_prompt = PromptRepositoryConfiguration(**prompt)

        return cls(inst_runner, inst_prompt)


#################################
# Application entities
#################################


@dataclass
class PromptConfiguration:
    name: str
    system_prompt: str
    user_prompt: str
    model: Optional[str] = None
