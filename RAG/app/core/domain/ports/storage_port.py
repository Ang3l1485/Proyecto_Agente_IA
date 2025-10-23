from abc import ABC, abstractmethod

class StoragePort(ABC):

    @abstractmethod
    def save_client_data(self,client_id: str,agent_id: str, prompt_modelo: str, metadata: str):
        raise NotImplementedError
    