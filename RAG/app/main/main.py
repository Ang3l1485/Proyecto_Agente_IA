from fastapi import FastAPI
from app.api.V1.routers.router_document import router as document_router
from app.api.V1.routers.router_messages import router as messages_router
from dotenv import load_dotenv


load_dotenv() 

app = FastAPI(title="AI Workflow Service", debug=True)

# Registro de los routers
app.include_router(document_router)
app.include_router(messages_router)

@app.get("/health")
def health():
    return {"status": "ok"}

