from abc import ABC, abstractmethod

class ClientRepositoryPort(ABC):
    @abstractmethod
    def save_info_document_client(self, client_id: str, agent_id: str, file_name: str, source_key: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_prompt_client(self, client_id: str, agent_id: str, prompt: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def get_prompt_client(self, client_id: str, agent_id: str) -> str | None:
        raise NotImplementedError
