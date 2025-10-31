
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException,BackgroundTasks
from pydantic import BaseModel, Field

# Pueros
from app.core.domain.ports.storage_port import StoragePort
from app.core.domain.ports.vector_port import VectorPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.ports.chunking_port import ChunkingPort

# Adaptadores
from app.infrastructure.adapters.minio_storage_adapter import MinioStorageAdapter
from app.infrastructure.adapters.qdrant_adapter import QdrantVectorAdapter
from app.infrastructure.adapters.openai_embedding_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.adapters.unstructed_langchain_chunking_adapter import UnstructuredLangChainChunkingAdapter

# Servicios

from app.application.process_document_service import ProcessingDocumentService
from app.application.storage_service import StorageService

from typing import BinaryIO

router=APIRouter(prefix="/document", tags=["documents"])

# 1) Provider del Puerto (devuelve el adaptador concreto)
def get_storage_port() -> StoragePort:
    try:
        return MinioStorageAdapter()
    except Exception as e:
        # Turns boot errors into a 500 with a clear message
        raise HTTPException(status_code=500, detail=f"Storage init error: {e}")
    
# 2) Provider del Servicio (inyecta el Puerto)
def get_storage_service(
    storage_port: StoragePort = Depends(get_storage_port),
) -> StorageService:
    return StorageService(storage_port)

def get_process_document_service(
    storage_port: StoragePort = Depends(get_storage_port),
    chunking_port: ChunkingPort = Depends(lambda: UnstructuredLangChainChunkingAdapter()),
    embedding_port: EmbeddingPort = Depends(lambda: OpenAIEmbeddingAdapter()),
    vector_port: VectorPort = Depends(lambda: QdrantVectorAdapter()),
) -> ProcessingDocumentService:
    return ProcessingDocumentService(
        storage_port=storage_port,
        chunking_port=chunking_port,
        embeddingPort=embedding_port,
        vector_port=vector_port,
        batch_size=128,
    )


# Se sube el documento y se activa la funnción de procesamiento en segundo plano
@router.post("/upload", summary="Subir un documento para un cliente y agente específicos")
async def upload_document(
    background_tasks: BackgroundTasks,
    client_id: str = Form(..., description="El ID que identifica al cliente"),
    agent_id: str = Form(..., description="El ID que identifica al agente"),
    token_auth: str = Form(..., description="Token de autenticación para el cliente"),
    file: UploadFile = File(..., description="El archivo a subir"),
    file_name: str = Form(..., description="Nombre del archivo"),
    service: StorageService = Depends(get_storage_service),
    process_service: ProcessingDocumentService = Depends(get_process_document_service),
):
    file_bytes = await file.read()

    object_key = service.save_document_client(
        client_id=client_id,
        agent_id=agent_id,
        token_auth=token_auth,
        file=file_bytes,
        file_name=file_name or file.filename,
    )

     # Define valores para vectorización
    collection = f"client_{client_id}"
    doc_id = object_key

    background_tasks.add_task(
        process_service.process_and_store_vector_document,
        object_key=object_key,
        file_name=file_name,
        client_id=client_id,
        agent_id=agent_id,
        collection=collection,
        doc_id=doc_id
    )

    
    return {
        "message": "Documento subido correctamente. Subiendo a la base vectorial en segundo plano.",
        "object_key": object_key
    }