from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VectorPort(ABC):
    @abstractmethod
    def up_embeddings(self, ids: List[str], vectors: List[List[float]], payloads: List[Dict[str, Any]], collection: str) -> None:
        """Inserta o actualiza embeddings en la colección especificada."""
        raise NotImplementedError

    @abstractmethod
    def search(self, vector: List[float], collection: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca los top_k puntos más cercanos al vector en la colección indicada."""
        raise NotImplementedError
    