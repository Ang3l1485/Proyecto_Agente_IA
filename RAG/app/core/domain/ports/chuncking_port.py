from abc import ABC, abstractmethod


class ChunckingPort(ABC):
    @abstractmethod
    def chunk_document(
        self,
        document_bytes: bytes,
        chunk_size: int,
        overlap_size: int
    ) -> list[str]:
        raise NotImplementedError