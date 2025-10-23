from abc import ABC, abstractmethod 

class WorkflowPort(ABC):
   
    @abstractmethod
    def run(self,input_text: str):

        raise NotImplementedError

    
