from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/message", tags=["messages"])

class RunRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to process with the OpenAI workflow")

class RunResponse(BaseModel):
    answer: str

@router.post("/response", response_model=RunResponse, summary="Process a user message through the OpenAI workflow")
async def process_message(
    message: str,
    agent_id: str,
    client_id:str,
    timestamp: str,
    cel_id: str,
):
    
    return print("No implementado aún")