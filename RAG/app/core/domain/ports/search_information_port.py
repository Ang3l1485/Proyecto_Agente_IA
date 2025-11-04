from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SearchInformationPort(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        pass