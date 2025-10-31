from abc import ABC, abstractmethod
from typing import List



class EmbeddingPort(ABC):


   # Puerto para la creación de embeddings.
   # Define la interfaz que cualquier adaptador de embeddings debe implementar.

    @abstractmethod
    def create_embeddings(self, texts: list[str] ) -> List[List[float]]:
        raise NotImplementedError