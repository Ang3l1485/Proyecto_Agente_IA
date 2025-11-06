from app.core.domain.ports.llm_port import LLMPort
from app.core.domain.ports.embedding_port import EmbeddingPort
from app.core.domain.ports.vector_port import VectorPort
from app.core.domain.ports.client_repository_port import ClientRepositoryPort
from app.core.domain.ports.chat_memory_port import ChatMemoryPort
from typing import Optional, List, Dict, Any
import time
import traceback


class ProcessQueryService:
    def __init__(
        self,
        response_llm: LLMPort,
        embedding_port: EmbeddingPort,
        vector_port: VectorPort,
        saveinfo_port: ClientRepositoryPort,
        prompt_ttl_seconds: int = 60,
        chat_memory: Optional[ChatMemoryPort] = None,
        history_limit: int = 20,
    ) -> None:
        self._response_llm = response_llm
        self._embedding_port = embedding_port
        self._vector_port = vector_port
        self._saveinfo_port = saveinfo_port
        self._prompt_ttl = prompt_ttl_seconds
        self._prompt_cache: dict[tuple[str, str], tuple[str | None, float]] = {}
        self._memory = chat_memory
        self._history_limit = history_limit
        
    # Caché simple de prompts por client_id y agent_id
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

    def _make_session_id(self, client_id: str, agent_id: str, client_cel: str) -> str:
        # Diferencia sesión por agente + número
        return f"{client_id}:{agent_id}:{client_cel}"

    def _candidate_collections(self, client_id: str, agent_id: str) -> List[str]:
        # Unifica estrategia y agrega fallback para entornos donde se mezcló client_id/agent_id
        return [
            f"client_{client_id}",
            f"client_{agent_id}",   # fallback si se indexó por agent_id por error
            # Si tu estrategia fuese por agente, invierte el orden de esta lista
            # f"agent_{agent_id}", f"agent_{client_id}",
        ]

    def process_query(self, query: str, client_id: str, agent_id: str, client_cel: str, timpestap: str, top_k: int = 5) -> str:
        # 0) Construir session id y recuperar historial reciente (solo Q/A previos)
        session_id = self._make_session_id(client_id=client_id, agent_id=agent_id, client_cel=client_cel)
        print(f"[query] start sid={session_id} top_k={top_k} q_len={len(query)} q_preview={query[:120]!r}")
        history: List[Dict[str, str]] = []
        if self._memory:
            try:
                history = self._memory.get_recent(session_id, limit=self._history_limit)
            except Exception as e:
                print(f"[query][warn] get_recent failed: {e}")
                traceback.print_exc()
                history = []
        print(f"[query] history_len={len(history)}")

        # 1) Embedding del query (siempre se recalcula)
        t0 = time.time()
        query_vec = self._embedding_port.create_embeddings([query])[0]
        t1 = time.time()
        dim = len(query_vec) if hasattr(query_vec, "__len__") else "unknown"
        print(f"[query] embedding computed dim={dim} dt_ms={int((t1-t0)*1000)}")

        # 2) Búsqueda vectorial probando colecciones candidatas
        matches: List[Dict[str, Any]] = []
        used_collection: Optional[str] = None

        for col in self._candidate_collections(client_id, agent_id):
            print(f"[query] vector search -> collection={col} top_k={top_k}")
            t2 = time.time()
            ctx = self._vector_port.search(vector=query_vec, collection=col, top_k=top_k)
            t3 = time.time()
            print(f"[query] vector search done dt_ms={int((t3-t2)*1000)} raw_type={type(ctx).__name__}")

            # normalizar a lista
            def _as_list(x) -> List[Dict[str, Any]]:
                if isinstance(x, list):
                    return x
                if isinstance(x, dict):
                    for k in ("points", "result", "matches"):
                        v = x.get(k)
                        if isinstance(v, list):
                            return v
                return []
            cand = _as_list(ctx)
            print(f"[query] matches_count in {col} = {len(cand)}")

            if cand:
                matches = cand
                used_collection = col
                break

        if not matches:
            print("[query][warn] 0 matches from all candidate collections")
        else:
            print(f"[query] using_collection={used_collection} matches={len(matches)}")
            # métricas del primer match
            sample = matches[0] if isinstance(matches, list) else {}
            payload = sample.get("payload", {}) if isinstance(sample, dict) else {}
            keys_preview = list(payload.keys())[:8] if isinstance(payload, dict) else []
            text_preview = None
            if isinstance(payload, dict):
                for k in ("text","content","page_content","text_preview"):
                    if payload.get(k):
                        text_preview = str(payload[k])[:160]
                        break
            score = sample.get("score") if isinstance(sample, dict) else None
            _id = sample.get("id") if isinstance(sample, dict) else None
            print(f"[query] first_match id={_id} score={score} payload_keys={keys_preview}")
            if text_preview is not None:
                print(f"[query] first_match text_preview={text_preview!r}")

        # 3) Prompt del agente (cacheado por TTL, no afecta a la búsqueda)
        system_prompt = self._get_prompt(client_id=client_id, agent_id=agent_id)
        sp_len = len(system_prompt) if system_prompt else 0
        print(f"[query] system_prompt_len={sp_len}")

        # 4) LLM con historial + contexto nuevo de esta búsqueda
        try:
            if hasattr(self._response_llm, "response_with_history"):
                answer = getattr(self._response_llm, "response_with_history")(  # type: ignore[attr-defined]
                    prompt=query,
                    history=history,
                    system_prompt=system_prompt,
                    context=matches,  # lista normalizada
                )
            else:
                answer = self._response_llm.response(prompt=query, context=matches, system_prompt=system_prompt)
        except Exception as e:
            print(f"[query][error] LLM call failed: {e}")
            traceback.print_exc()
            raise

        ans_len = len(answer) if isinstance(answer, str) else 0
        print(f"[query] answer_len={ans_len} answer_preview={str(answer)[:200]!r}")

        # 5) Persistir SOLO pregunta y respuesta en la memoria
        if self._memory:
            try:
                self._memory.append(session_id, "user", query)
                self._memory.append(session_id, "assistant", answer)
                print(f"[query] memory appended (user+assistant) for sid={session_id}")
            except Exception as e:
                print(f"[query][warn] memory append failed: {e}")
                traceback.print_exc()

        print("[query] end")
        return answer





