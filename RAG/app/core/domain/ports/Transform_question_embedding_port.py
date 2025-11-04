from abc import ABC, abstractmethod

class TransformQuestionEmbeddingPort(ABC):
    @abstractmethod
    def transform(self, question: str) -> list[float]:
        raise NotImplementedError
    
    