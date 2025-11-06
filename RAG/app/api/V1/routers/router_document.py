# app/api/V1/routers/router_document.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from typing import Annotated

# Importar los puertos y adaptadores necesarios
from app.core.domain.ports.storage_port import StoragePort
from app.core.domain.ports.vector_port import VectorPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.ports.chunking_port import ChunkingPort
from app.core.domain.ports.client_repository_port import ClientRepositoryPort as SaveInfoClientPort
# los adaptadores
from app.infrastructure.adapters.minio_storage_adapter import MinioStorageAdapter
from app.infrastructure.adapters.qdrant_adapter import QdrantVectorAdapter
from app.infrastructure.adapters.openai_embedding_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.adapters.langchain_chunking_adapter import LangChainChunkingAdapter
from app.infrastructure.adapters.postgres_saveinfo_adapter import PostgresSaveInfoClientAdapter
# El servicio de procesamiento
from app.application.process_document_service import ProcessingDocumentService
from app.application.storage_service import StorageService

router = APIRouter(prefix="/document", tags=["documents"])

def get_storage_port() -> StoragePort:
    try:
        return MinioStorageAdapter()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage init error: {e}")

def get_storage_service(storage_port: StoragePort = Depends(get_storage_port)) -> StorageService:
    return StorageService(storage_port)
def get_process_document_service(
    storage_port: StoragePort = Depends(get_storage_port),
    chunking_port: ChunkingPort = Depends(lambda: LangChainChunkingAdapter()),
    embedding_port: EmbeddingPort = Depends(lambda: OpenAIEmbeddingAdapter()),
    vector_port: VectorPort = Depends(lambda: QdrantVectorAdapter()),
    save_info_port: SaveInfoClientPort = Depends(lambda: PostgresSaveInfoClientAdapter()),
) -> ProcessingDocumentService:
    return ProcessingDocumentService(
        storage_port=storage_port,
        chunking_port=chunking_port,
        embeddingPort=embedding_port,
        vector_port=vector_port,
        save_info=save_info_port,
        batch_size=128,
    )

@router.post("/upload", summary="Subir documento y/o actualizar prompt del agente")
async def upload_document(
    background_tasks: BackgroundTasks,
    client_id: Annotated[str, Form()],                 # requerido
    agent_id: Annotated[str, Form()],                  # requerido
    token_auth: Annotated[str, Form()],                # requerido
    file: Annotated[UploadFile | None, File()] = None, # opcional (UploadFile para .read() y .filename)
    file_name: Annotated[str | None, Form()] = None,   # opcional
    prompt: Annotated[str | None, Form()] = None,      # opcional
    storage_svc: StorageService = Depends(get_storage_service),
    proc_svc: ProcessingDocumentService = Depends(get_process_document_service),
):
    if not file and not (prompt and prompt.strip()):
        raise HTTPException(status_code=400, detail="Debe enviar un archivo o un prompt (o ambos).")

    object_key = None
    if file is not None:
        file_bytes = await file.read()
        # Tratar archivo vacío como "sin archivo"
        if file_bytes and len(file_bytes) > 0:
            object_key = storage_svc.save_document_client(
                client_id=client_id,
                agent_id=agent_id,
                token_auth=token_auth,
                file=file_bytes,
                file_name=(file_name or file.filename),
            )
        else:
            file = None  # equivale a no enviar archivo

    collection = f"client_{client_id}"
    doc_id = object_key or ""

    background_tasks.add_task(
        proc_svc.process_and_store_vector_document,
        object_key=object_key,
        file_name=(file_name or (file.filename if file else None)),
        client_id=client_id,
        agent_id=agent_id,
        collection=collection,
        doc_id=doc_id,
        prompt=prompt,
    )
    return {"message": "Tarea encolada", "object_key": object_key}