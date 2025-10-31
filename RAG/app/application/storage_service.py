# app/application/services/storage_service.py
import os
import mimetypes
from typing import Optional
from app.core.domain.ports.storage_port import StoragePort

class StorageService:


    def __init__(self, storage_port: StoragePort) -> None:
        self._storage = storage_port
        # Limite de tamaño de archivo en bytes (por ejemplo, 20 MB) (se puede configurar vía env)
        self._max_bytes = int(os.getenv("UPLOAD_MAX_BYTES", str(20 * 1024 * 1024)))  # 20 MB

        
    #Utiliza el puerto para guardar el documento de un cliente
    def save_document_client(
        self,
        *,
        client_id: str,
        agent_id: str,
        token_auth: str,
        file: bytes,
        file_name: str
    ) -> str:

        object_key = self._storage.save_document_client(
            client_id=client_id,
            agent_id=agent_id,
            token_auth=token_auth,
            file=file,
            file_name=file_name
        )

    
        return object_key
