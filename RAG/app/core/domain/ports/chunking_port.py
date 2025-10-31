# app/core/domain/ports/chunking_port.py
from typing import Iterable
from app.core.domain.models import Chunk

class ChunkingPort:
    def split_file(self, file_bytes: bytes, file_name: str, base_metadata: dict) -> Iterable[Chunk]:
        raise NotImplementedError