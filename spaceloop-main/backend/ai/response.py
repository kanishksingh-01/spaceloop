from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AIResponse:
    content: str
    metadata: Dict[str, Any]
