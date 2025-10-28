from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException,BackgroundTasks
from pydantic import BaseModel, Field
from app.application.storage_service import StorageService
from app.core.domain.ports.storage_port import StoragePort
from app.infrastructure.adapters.minio_storage_adapter import MinioStorageAdapter

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

@router.post("/upload", summary="Subir un documento para un cliente y agente específicos")
async def upload_document(
    client_id: str = Form(..., description="El ID que identifica al cliente"),
    agent_id: str = Form(..., description="El ID que identifica al agente"),
    token_auth: str = Form(..., description="Token de autenticación para el cliente"),
    file: UploadFile = File(..., description="El archivo a subir"),
    file_name: str = Form(..., description="Nombre del archivo"),
    service: StorageService = Depends(get_storage_service),  # <-- inyectado aquí
):
    file_bytes = await file.read()

    object_key = service.save_document_client(
        client_id=client_id,
        agent_id=agent_id,
        token_auth=token_auth,
        file=file_bytes,
        file_name=file_name or file.filename,
    )

    
    return {"message": "Uploaded", "object_key": object_key}