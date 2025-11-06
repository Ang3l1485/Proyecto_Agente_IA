from app.core.domain.ports.llm_port import LLMPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.ports.vector_port import VectorPort
from app.core.domain.ports.client_repository_port import ClientRepositoryPort
import time


class ProcessQueryService:
    def __init__(self, response_llm: LLMPort, embedding_port: EmbeddingPort, vector_port: VectorPort, saveinfo_port: ClientRepositoryPort, prompt_ttl_seconds: int = 60) -> None:
        self._response_llm = response_llm
        self._embedding_port = embedding_port
        self._vector_port = vector_port
        self._saveinfo_port = saveinfo_port
        self._prompt_ttl = prompt_ttl_seconds
        self._prompt_cache: dict[tuple[str, str], tuple[str | None, float]] = {}

    def _get_prompt(self, client_id: str, agent_id: str) -> str | None:
        key = (client_id, agent_id)
        now = time.time()
        cached = self._prompt_cache.get(key)
        if cached:
            value, ts = cached
            if now - ts < self._prompt_ttl:
                return value
        value = self._saveinfo_port.get_prompt_client(client_id=client_id, agent_id=agent_id)
        self._prompt_cache[key] = (value, now)
        return value

    def process_query(self, query: str, client_id: str, agent_id: str, client_cel: str, timpestap: str, top_k: int = 5) -> str:
        # 1) Convertir el query en embedding
        query_embedding = self._embedding_port.create_embeddings([query])[0]

        # 2) Buscar en la base de datos vectorial
        collection = f"client_{client_id}"
        context = self._vector_port.search(vector=query_embedding, collection=collection, top_k=top_k)

        # 3) Generar la respuesta con el LLM
        system_prompt = self._get_prompt(client_id=client_id, agent_id=agent_id)
        answer = self._response_llm.response(prompt=query, context=context, system_prompt=system_prompt)
        return answer





