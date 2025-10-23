from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.infrastructure.adapters.openai_workflow_adapter import OpenAIWorkflowAdapter
from app.infrastructure.config.settings import settings
import logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/message", tags=["messages"])

class RunRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to process with the OpenAI workflow")

class RunResponse(BaseModel):
    answer: str

def get_adapter() -> OpenAIWorkflowAdapter:
    # Minimal: crear el adaptador por solicitud.
    # Cuando tengas lifespan, lo movemos allí para reusar instancia.
    return OpenAIWorkflowAdapter(settings)
