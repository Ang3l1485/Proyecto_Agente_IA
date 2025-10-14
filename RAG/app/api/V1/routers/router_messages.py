from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.infrastructure.adapters.openai_workflow_adapter import OpenAIWorkflowAdapter
from app.infrastructure.config.settings import settings

router = APIRouter(prefix="/message", tags=["messages"])

class RunRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to process with the OpenAI workflow")

class RunResponse(BaseModel):
    answer: str

def get_adapter() -> OpenAIWorkflowAdapter:
    # Minimal: crear el adaptador por solicitud.
    # Cuando tengas lifespan, lo movemos allí para reusar instancia.
    return OpenAIWorkflowAdapter(settings)

@router.post("/run", response_model=RunResponse)
async def run_workflow(req: RunRequest, adapter: OpenAIWorkflowAdapter = Depends(get_adapter)):
    try:
        # Tu adapter.run es async -> hay que await
        result = await adapter.run(input_text=req.message)
        # Tu adapter retorna un dict {"answer": ..., "sources": ..., "meta": ...}
        return RunResponse(answer=result.get("answer", ""))
    except Exception as e:
        # (Opcional) log interno aquí
        raise HTTPException(status_code=500, detail="Workflow invocation failed")
