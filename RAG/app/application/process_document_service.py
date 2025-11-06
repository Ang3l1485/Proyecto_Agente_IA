# app/application/process_document_service.py
import os, traceback
from typing import Iterable, List, Optional, Dict
from app.core.domain.models import Chunk
from app.core.domain.ports.storage_port import StoragePort
from app.core.domain.ports.chunking_port import ChunkingPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.ports.vector_port import VectorPort
from app.core.domain.ports.client_repository_port import ClientRepositoryPort as SaveInfoClientPort

class ProcessingDocumentService:
    def __init__(
        self,
        storage_port: StoragePort,
        chunking_port: ChunkingPort,
        embeddingPort: EmbeddingPort,
        vector_port: VectorPort,
        save_info: SaveInfoClientPort,
        batch_size: int = 128,
    ) -> None:
        self._storage = storage_port
        self._chunking = chunking_port
        self._embedding = embeddingPort
        self._vectors = vector_port
        self._saveinfo = save_info
        self._batch_size = batch_size
        self.INCLUDE_FULL_TEXT_IN_PAYLOAD = os.getenv("INCLUDE_FULL_TEXT_IN_PAYLOAD", "false").lower() == "true"
        self.MAX_PAYLOAD_CHARS = int(os.getenv("PAYLOAD_PREVIEW_CHARS", "800"))

    def _batched(self, iterable: Iterable[Chunk], n: int) -> Iterable[List[Chunk]]:
        batch: List[Chunk] = []
        for item in iterable:
            batch.append(item)
            if len(batch) == n:
                yield batch; batch = []
        if batch:
            yield batch

    def process_and_store_vector_document(
        self,
        *,
        object_key: Optional[str] = None,
        file_name: Optional[str] = None,
        collection: Optional[str] = None,
        # Identificación del cliente/agente
        client_id: str,
        agent_id: str,
        doc_id: Optional[str] = None,
        # Construcción del prompt
        prompt: Optional[str] = None,
    ) -> Dict[str, int | bool]:
        print("=== process_and_store_vector_document: START ===")
        indexed_total = 0
        prompt_updated = False

        # --- A) Procesar DOCUMENTO (solo si object_key viene) ---
        if object_key:
            try:
                print("[storage] downloading...")
                document_bytes = self._storage.get_document_client(object_key=object_key)
                print(f"[storage] bytes={len(document_bytes) if document_bytes else 0}")
            except Exception as e:
                print(f"[error:storage] {e}"); traceback.print_exc(); raise

            metadata_base = {
                "client_id": client_id,
                "agent_id": agent_id,
                "source": object_key,
                "doc_id": doc_id or object_key,
                "file_name": file_name or "",
            }

            try:
                chunks_iter = self._chunking.split_file(
                    file_bytes=document_bytes,
                    file_name=file_name or "file.pdf",
                    base_metadata=metadata_base,
                )
            except Exception as e:
                print(f"[error:chunking] {e}"); traceback.print_exc(); raise

            batch_index = 0
            try:
                for batch in self._batched(chunks_iter, self._batch_size):
                    batch_index += 1
                    ids, texts, payloads = [], [], []
                    for c in batch:
                        full_text = (c.content or "").strip()
                        if not full_text:
                            continue
                        ids.append(c.id); texts.append(full_text)
                        payload = dict(c.metadata or {})
                        payload["text_preview"] = full_text[: self.MAX_PAYLOAD_CHARS]
                        payload["has_more"] = len(full_text) > self.MAX_PAYLOAD_CHARS
                        if self.INCLUDE_FULL_TEXT_IN_PAYLOAD:
                            payload["text"] = full_text
                        payloads.append(payload)

                    if not ids:
                        continue

                    vectors = self._embedding.create_embeddings(texts)
                    self._vectors.up_embeddings(ids=ids, vectors=vectors, payloads=payloads, collection=collection or f"client_{client_id}")
                    indexed_total += len(ids)

                # registrar en Postgres el documento procesado
                try:
                    if prompt is not None and prompt.strip():
                        self._saveinfo.save_info_document_client(
                            client_id=client_id,
                            agent_id=agent_id,
                            file_name=file_name or "",
                            source_key=object_key,
                        )
                    else:
                        print("[saveinfo] prompt no viene o está vacío, no se guarda info documento")
                except Exception as e:
                    print(f"[warn:saveinfo:document] {e}")

            except Exception as e:
                print(f"[error:vectorize-loop] {e}"); traceback.print_exc(); raise

        # --- B) Actualizar PROMPT (solo si viene y no está vacío) ---
        if prompt is not None and prompt.strip():
            try:
                self._saveinfo.save_prompt_client(client_id=client_id, agent_id=agent_id, prompt=prompt.strip())
                prompt_updated = True
            except Exception as e:
                print(f"[error:saveinfo:prompt] {e}"); traceback.print_exc(); raise

        print(f"=== END (indexed_chunks={indexed_total}, prompt_updated={prompt_updated}) ===")
        return {"indexed_chunks": indexed_total, "prompt_updated": prompt_updated}
