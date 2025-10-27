from abc import ABC, abstractmethod

class StoragePort(ABC):

    @abstractmethod
    def save_document_client(
        self,client_id: str,
        agent_id: str,
        token_auth: str,
        file: bytes, 
        file_name: str) -> str:
        
        raise NotImplementedError
    