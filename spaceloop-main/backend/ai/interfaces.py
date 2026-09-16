from typing import Protocol, Dict, Any

class AIProvider(Protocol):
    def complete(self, prompt: str) -> str:
        ...
