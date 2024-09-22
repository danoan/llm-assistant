from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMAssistantConfiguration:
    openai_key: Optional[str] = None
    model: Optional[str] = None
    use_cache: bool = False
    cache_path: Optional[str] = None
    prompt_repository: Optional[Dict[str, Any]] = None

    def __str__(self):
        return (
            f"openai_key: <<HIDDEN>>\n"
            f"model: {self.model}\n"
            f"use_cache: {self.use_cache}\n"
            f"cache_path: {self.cache_path}\n"
            f"prompt_repository: {self.prompt_repository}\n"
        )


@dataclass
class PromptConfiguration:
    name: str
    system_prompt: str
    user_prompt: str
    model: Optional[str] = None
