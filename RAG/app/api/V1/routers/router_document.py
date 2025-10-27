from fastapi import APIRouter, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field
from app.application.storage_service import StorageService
from app.core.domain.ports.storage_port import StoragePort
from app.infrastructure.adapters.minio_storage_adapter import MinioStorageAdapter

from typing import BinaryIO

app=APIRouter(prefix="/document", tags=["documents"])

# 1) Provider del Puerto (devuelve el adaptador concreto)
def get_storage_port() -> StoragePort:
    return MinioStorageAdapter()  # usa env vars dentro

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

    object_key = service.upload_document(
        client_id=client_id,
        agent_id=agent_id,
        token_auth=token_auth,
        file_bytes=file_bytes,
        file_name=file_name or file.filename,
    )
    return {"message": "Uploaded", "object_key": object_key}