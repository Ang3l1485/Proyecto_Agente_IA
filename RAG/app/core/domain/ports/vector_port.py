from abc import ABC, abstractmethod
from typing import List


class VectorPort(ABC):
    @abstractmethod
    def up_embeddings(self, ids=str, vectors=list[float], payloads=list[str], collection=str) -> None:
        raise NotImplementedError
    