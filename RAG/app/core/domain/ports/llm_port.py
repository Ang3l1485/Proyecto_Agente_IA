from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMPort(ABC):
    @abstractmethod
    def response(self, prompt: str, context: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> str:
        """Genera una respuesta textual; `system_prompt` permite personalizar el rol/estilo por agente."""
        raise NotImplementedError
    