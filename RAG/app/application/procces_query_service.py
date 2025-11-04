from app.core.domain.ports.search_information_port import SearchInformationPort
from RAG.app.core.domain.ports.response_llm_response_port import ResponseLlmPort

class ProcessQueryService:
    def __init__(self, search_port: SearchInformationPort, response_llm:ResponseLlmPort) -> str:
       
        self._search_port = search_port
        self._response_llm = response_llm
    
    def process_query(self, query: str, client_id: str, agent_id: str, client_cel: str, timpestap: str, top_k: int = 5) -> str:

        # Convertir el query en embedding y buscar en vector DB
        

        
        context = self._search_port.search(query=query, top_k=top_k)

    
        answer = self._response_llm.response(prompt=query, context=context)

        return answer





