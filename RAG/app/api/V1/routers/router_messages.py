from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

from app.application.procces_query_service import ProcessQueryService
from app.infrastructure.adapters.llm_adapter import OpenAILLMAdapter
from app.infrastructure.adapters.openai_embedding_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.adapters.qdrant_adapter import QdrantVectorAdapter
from app.infrastructure.adapters.postgres_saveinfo_adapter import PostgresSaveInfoClientAdapter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/message", tags=["messages"])


class RunRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    agent_id: str
    client_id: str
    timestamp: str
    cel_id: str


class RunResponse(BaseModel):
    answer: str


def get_process_query_service() -> ProcessQueryService:
    try:
        llm = OpenAILLMAdapter()
        embed = OpenAIEmbeddingAdapter()
        vector = QdrantVectorAdapter()
        repo = PostgresSaveInfoClientAdapter()
        return ProcessQueryService(response_llm=llm, embedding_port=embed, vector_port=vector, saveinfo_port=repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Init error: {e}")


@router.post("/response", response_model=RunResponse, summary="Process a user message with RAG and per-agent prompt")
async def process_message(req: RunRequest, svc: ProcessQueryService = Depends(get_process_query_service)):
    try:
        answer = svc.process_query(
            query=req.message,
            client_id=req.client_id,
            agent_id=req.agent_id,
            client_cel=req.cel_id,
            timpestap=req.timestamp,
        )
        return RunResponse(answer=answer)
    except Exception as e:
        logger.exception("process_message failed")
        raise HTTPException(status_code=500, detail=str(e))