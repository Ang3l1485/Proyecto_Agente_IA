from typing import Dict, List
from threading import RLock
from app.core.domain.ports.chat_memory_port import ChatMemoryPort

class InMemoryChatMemoryAdapter(ChatMemoryPort):
    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, str]]] = {}
        self._lock = RLock()

    def get_recent(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        with self._lock:
            msgs = self._store.get(session_id, [])
            return msgs[-limit:].copy()

    def append(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._store.setdefault(session_id, []).append({"role": role, "content": content})

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)