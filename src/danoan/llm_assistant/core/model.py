from dataclasses import dataclass


@dataclass
class PromptConfiguration:
    name: str
    system_prompt: str
    user_prompt: str
