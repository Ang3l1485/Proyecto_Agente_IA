
import os
import io
import time
import unicodedata
from typing import Optional
from minio import Minio
from minio.error import S3Error


from app.core.domain.ports import storage_port

def _limpiar_nombre_archivo(nombre: str) -> str:
    #Como minio no soporta ciertos caracteres en los nombres de archivo, limpiamos el nombre con la estructura que
    # acepta S3
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode('ascii')
    nfkd = unicodedata.normalize("NFKD", nombre)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    safe = ascii_name.replace(" ", "_")
    return "".join(ch for ch in safe if ch.isalnum() or ch in ("_", ".", "-", "+"))

class MinioStorageAdapter(storage_port.StoragePort):

    def __init__(
            self,
            endpoint: Optional[str] = None,
            user_key: Optional[str] = None,
            password_key: Optional[str] = None,
            bucket_name: Optional[str] = None,
            secure: bool=False
        ) -> None:
        self.endpoint = os.getenv("MINIO_API_PORT")
        self.user_key= os.getenv("MINIO_ROOT_USER")
        self.password_key= os.getenv("MINIO_ROOT_PASSWORD")
        self.bucket_name= os.getenv("MINIO_BUCKET_NAME")
        
        #Creo el cliente de Minio
        self.client = Minio(
        self.endpoint,
        self.user_key,
        self.password_key,
        secure=False
        )

    def _ensure_bucket(self) -> None:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
    #Guarda el documento de un cliente en minio
    def save_document_client(
        self,client_id: str,
        agent_id: str,
        token_auth: str,
        file: bytes, 
        file_name: str) -> str:

        # Asegurarse de que el bucket exista
        self._ensure_bucket()

        # Limpiar el nombre del archivo
        safe_file_name = _limpiar_nombre_archivo(file_name)

        # Crear un nombre de objeto único en el bucket
        timestamp = int(time.time())
        object_name = f"{client_id}/{agent_id}/{timestamp}_{safe_file_name}"

        # Subir el archivo a Minio
        file_size = len(file)
        file_stream = io.BytesIO(file)
        print(f"[minio] put_object bucket={self.bucket_name} key={object_name} size={file_size}")
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=file_stream,
            length=file_size,
            content_type="application/octet-stream"
        )
        print(f"[minio] uploaded key={object_name}")
        return object_name
    
    # Obtiene el documento de un cliente desde minio
    def get_document_client(
        self,
        object_key: str
    ) -> bytes:
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Error retrieving document: {e}")