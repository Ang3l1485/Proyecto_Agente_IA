from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ResponseLlmPort(ABC):
    @abstractmethod
    def response(self, prompt: str, context: List[Dict[str, Any]]) -> str:
        pass