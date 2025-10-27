from fastapi import FastAPI
from app.api.V1.routers.router_messages import router as message_router
from app.api.V1.routers.router_document import app as document_router

app = FastAPI(title="AI Workflow Service", debug=True)

# Registro de los routers
app.include_router(message_router)
app.include_router(document_router)

@app.get("/health")
def health():
    return {"status": "ok"}



