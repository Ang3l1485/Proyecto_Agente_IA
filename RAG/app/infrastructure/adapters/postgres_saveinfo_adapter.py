# app/infrastructure/adapters/postgres_saveinfo_adapter.py
from __future__ import annotations

import os
import uuid
from typing import Optional
import psycopg
from psycopg_pool import ConnectionPool
from app.core.domain.ports.client_repository_port import ClientRepositoryPort as SaveInfoClientPort

def _dsn_from_env() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB", "agentes")
    user = os.getenv("POSTGRES_USER", "admin")
    pwd  = os.getenv("POSTGRES_PASSWORD", "user123")
    schema = os.getenv("POSTGRES_SCHEMA", "rag")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}?options=-c%20search_path%3D{schema}"
#-----------------------------------------------por si hay que quitarlo-----------------
def _schema_from_env() -> str:
    return os.getenv("POSTGRES_SCHEMA", "rag")
#-------------------------------------------------------------------------------------------


class PostgresSaveInfoClientAdapter(SaveInfoClientPort):
    def __init__(self, dsn: Optional[str] = None, min_size: int = 1, max_size: int = 5) -> None:
        self._dsn = dsn or _dsn_from_env()
        self._pool = ConnectionPool(self._dsn, min_size=min_size, max_size=max_size, kwargs={"autocommit": True})
#---------------------------------------------------------------
        # Asegurar que el esquema/tablas necesarias existan
        try:
            self._ensure_schema()
        except Exception as e:
            # No impedir el arranque; registrar y continuar (las operaciones fallarán si realmente falta permiso)
            print(f"[warn:postgres:init] no se pudo asegurar el esquema/tablas: {e}")

    def _ensure_schema(self) -> None:
        schema = _schema_from_env()
        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS {schema};
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS agents (
            client_id TEXT NOT NULL,
            id TEXT NOT NULL,
            PRIMARY KEY (client_id, id)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY,
            client_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            source_key TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS prompts (
            client_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (client_id, agent_id)
        );
        """
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(ddl)
#--------------------------------------------------
    def save_info_document_client(self, client_id: str, agent_id: str, file_name: str, source_key: str | None = None) -> None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO clients (id) VALUES (%s) ON CONFLICT (id) DO NOTHING""", (client_id,))
            cur.execute("""INSERT INTO agents (client_id, id) VALUES (%s, %s) ON CONFLICT (client_id, id) DO NOTHING""", (client_id, agent_id))
            cur.execute(
                """INSERT INTO documents (id, client_id, agent_id, file_name, source_key)
                   VALUES (%s, %s, %s, %s, %s)""",
                (str(uuid.uuid4()), client_id, agent_id, file_name, source_key),
            )

    def save_prompt_client(self, client_id: str, agent_id: str, prompt: str) -> None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO clients (id) VALUES (%s) ON CONFLICT (id) DO NOTHING""", (client_id,))
            cur.execute("""INSERT INTO agents (client_id, id) VALUES (%s, %s) ON CONFLICT (client_id, id) DO NOTHING""", (client_id, agent_id))
            cur.execute(
                """INSERT INTO prompts (client_id, agent_id, prompt, updated_at)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (client_id, agent_id)
                   DO UPDATE SET prompt = EXCLUDED.prompt, updated_at = NOW()""",
                (client_id, agent_id, prompt),
            )

    def get_prompt_client(self, client_id: str, agent_id: str) -> str | None:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute("""SELECT prompt FROM prompts WHERE client_id = %s AND agent_id = %s""", (client_id, agent_id))
            row = cur.fetchone()
            return row[0] if row else None
