from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMAssistantConfiguration:
    openai_key: Optional[str] = None
    use_cache: bool = False
    cache_path: Optional[str] = None

    def __str__(self):
        return (
            f"openai_key: <<HIDDEN>>\n"
            f"use_cache: {self.use_cache}\n"
            f"cache_path {self.cache_path}\n"
        )


@dataclass
class PromptConfiguration:
    name: str
    system_prompt: str
    user_prompt: str
