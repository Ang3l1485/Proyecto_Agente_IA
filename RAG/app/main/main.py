from fastapi import FastAPI
from app.api.V1.routers.router_messages import router as message_router

app = FastAPI(title="AI Workflow Service", debug=True)

# Registrar tu router
app.include_router(message_router)

@app.get("/health")
def health():
    return {"status": "ok"}
