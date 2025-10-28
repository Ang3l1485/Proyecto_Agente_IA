from abc import ABC, abstractmethod

class StoragePort(ABC):
    #Guardar el documento de un cliente 
    @abstractmethod
    def save_document_client(
        self,client_id: str,
        agent_id: str,
        token_auth: str,
        file: bytes, 
        file_name: str) -> str:
        
        raise NotImplementedError
    #Guardar el documento en una base vectorial para un agente
    