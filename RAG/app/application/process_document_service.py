from app.core.domain.ports.storage_port import StoragePort
from app.core.domain.ports.chuncking_port import ChunkingPort


class processing_document_service:
    def __init__(self, storage_port: StoragePort, chunking_port: ChunkingPort) -> None:
        self._storage = storage_port
        self._chunking = chunking_port