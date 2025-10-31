from app.core.domain.ports.storage_port import StoragePort
from app.core.domain.ports.chuncking_port import ChunkingPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.models import chunk
from typing import Iterable, List, Dict


class ProcessingDocumentService:
    def __init__(self, storage_port: StoragePort, chunking_port: ChunkingPort, embeddingPort: EmbeddingPort,  batch_size =128 ) -> None:
        self._storage = storage_port
        self._chunking = chunking_port
        self._embedding = embeddingPort
        self._batch_size = batch_size  # Tamaño del lote para procesamiento por lotes
    
     #--- Función para dividir en lotes ---
    def _batched(self, iterable: Iterable[chunk], n: int) -> Iterable[List[chunk]]:
            batch: List[chunk] = []
            for item in iterable:
                batch.append(item)
                if len(batch) == n:
                    yield batch
                    batch = []
            if batch:
                yield batch

    def process_and_store_vector_document(self,object_key: str, file_name: str, client_id:str, agent_id:str, collection: str, doc_id: str) : #-> str
        # 1) obtener el documento desde el almacenamiento (Minio en este caso)
        document_bytes = self._storage.get_document_client(object_key=object_key)

        metadata_base = {
            "client_id": client_id,
            "agent_id": agent_id,
            "source": object_key,
        }


        # 2) Dividir el documento en chunks
        chunks_iter: Iterable[chunk] = self._chunking.split_file(
            file_bytes=document_bytes,
            file_name=file_name,
            base_metadata=metadata_base,
        )

        # 3) se convierten en embeddings y se almacenan en la base vectorial

        total = 0
        for batch in self._batched(chunks_iter, self._batch_size):
            ids = [c.id for c in batch]
            texts = [c.text for c in batch]
            payloads = [c.metadata for c in batch]

            vectors = self._embedding.create_embeddings(texts)

            self._vectors.up_embeddings(ids=ids, vectors=vectors, payloads=payloads, collection=collection)
            total += len(batch)

        return {"indexed_chunks": total}


