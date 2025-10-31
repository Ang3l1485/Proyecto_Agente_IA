from app.core.domain.ports.storage_port import StoragePort
<<<<<<< HEAD
from app.core.domain.ports.chuncking_port import ChunkingPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.models import chunk
from typing import Iterable, List, Dict


class ProcessingDocumentService:
    def __init__(self, storage_port: StoragePort, chunking_port: ChunkingPort, embeddingPort: EmbeddingPort,  batch_size =128 ) -> None:
=======
from app.core.domain.ports.chunking_port import ChunkingPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.ports.vector_port import VectorPort
from app.core.domain.models import Chunk
from typing import Iterable, List, Dict
import traceback  # <-- agregado

class ProcessingDocumentService:
    def __init__(self, storage_port: StoragePort, chunking_port: ChunkingPort, embeddingPort: EmbeddingPort, vector_port: VectorPort,  batch_size =128 ) -> None:
>>>>>>> 47666bc8847d239cbe570259fa3d186bbe2e6fe7
        self._storage = storage_port
        self._chunking = chunking_port
        self._embedding = embeddingPort
        self._batch_size = batch_size  # Tamaño del lote para procesamiento por lotes
<<<<<<< HEAD
    
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
=======
        self._vectors = vector_port
    
     #--- Función para dividir en lotes ---
    def _batched(self, iterable: Iterable[Chunk], n: int) -> Iterable[List[Chunk]]:
            batch: List[Chunk] = []
            for item in iterable:
                batch.append(item)
                if len(batch) == n:
                    # debug
                    try:
                        print(f"[batch] Listo para procesar lote de tamaño: {len(batch)}")
                    except Exception:
                        pass
                    yield batch
                    batch = []
            if batch:
                # debug
                try:
                    print(f"[batch] Listo para procesar último lote de tamaño: {len(batch)}")
                except Exception:
                    pass
                yield batch

    def process_and_store_vector_document(self,object_key: str, file_name: str, client_id:str, agent_id:str, collection: str, doc_id: str) : #-> str
        print("=== process_and_store_vector_document: INICIO ===")
        print(f"Params -> object_key={object_key}, file_name={file_name}, client_id={client_id}, agent_id={agent_id}, collection={collection}, batch_size={self._batch_size}")
        try:
            # 1) obtener el documento desde el almacenamiento (Minio en este caso)
            print("[step:storage] Descargando documento desde almacenamiento...")
            document_bytes = self._storage.get_document_client(object_key=object_key)
            print(f"[step:storage] Documento descargado. Bytes: {len(document_bytes) if document_bytes is not None else 'None'}")
        except Exception as e:
            print(f"[error:storage] Error obteniendo documento: {e}")
            traceback.print_exc()
            raise
>>>>>>> 47666bc8847d239cbe570259fa3d186bbe2e6fe7

        metadata_base = {
            "client_id": client_id,
            "agent_id": agent_id,
            "source": object_key,
        }

<<<<<<< HEAD

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

=======
        try:
            # 2) Dividir el documento en chunks
            print("[step:chunking] Iniciando chunking (streaming)...")
            chunks_iter: Iterable[Chunk] = self._chunking.split_file(
                file_bytes=document_bytes,
                file_name=file_name,
                base_metadata=metadata_base,
            )
        except Exception as e:
            print(f"[error:chunking] Error preparando el iterador de chunks: {e}")
            traceback.print_exc()
            raise

        # 3) se convierten en embeddings y se almacenan en la base vectorial
        total = 0
        batch_index = 0
        try:
            for batch in self._batched(chunks_iter, self._batch_size):
                batch_index += 1
                print(f"[step:batch:{batch_index}] Chunking entregó lote con {len(batch)} chunks")
                try:
                    ids = [c.id for c in batch]
                    # Nota: el servicio ya usa c.text en la lógica original; mantenemos esa línea.
                    texts = [c.text for c in batch]
                    payloads = [c.metadata for c in batch]

                    print(f"[step:embedding:{batch_index}] Creando embeddings para {len(texts)} textos...")
                    vectors = self._embedding.create_embeddings(texts)
                    dim = len(vectors[0]) if vectors and vectors[0] is not None else 0
                    print(f"[step:embedding:{batch_index}] Embeddings creados: {len(vectors)} vectores. Dimensión: {dim}")

                    print(f"[step:upsert:{batch_index}] Upsert en Qdrant -> collection='{collection}', puntos={len(ids)}")
                    self._vectors.up_embeddings(ids=ids, vectors=vectors, payloads=payloads, collection=collection)
                    total += len(batch)
                    print(f"[step:upsert:{batch_index}] Upsert OK. Total acumulado: {total}")
                except Exception as e:
                    print(f"[error:batch:{batch_index}] Error procesando el lote: {e}")
                    traceback.print_exc()
                    raise
        except Exception as e:
            print(f"[error:loop] Error durante la iteración de lotes: {e}")
            traceback.print_exc()
            raise

        print(f"=== process_and_store_vector_document: FIN (indexed_chunks={total}) ===")
>>>>>>> 47666bc8847d239cbe570259fa3d186bbe2e6fe7
        return {"indexed_chunks": total}


