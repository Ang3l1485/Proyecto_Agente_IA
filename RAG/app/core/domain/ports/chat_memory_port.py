from abc import ABC, abstractmethod
from typing import List, Dict

class ChatMemoryPort(ABC):
    @abstractmethod
    def get_recent(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def append(self, session_id: str, role: str, content: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self, session_id: str) -> None:
        raise NotImplementedError