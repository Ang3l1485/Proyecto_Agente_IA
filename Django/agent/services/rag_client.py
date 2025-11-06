import requests
from django.conf import settings


def ingest_document(
    *,
    business_id: str,
    agent_id: str,
    token_auth: str | None,
    document_id: str | None,
    file_path: str,
    file_name: str,
    content_type: str | None = None,
):
    """Upload a file to the RAG service using the router defined in router_document.py.

    Note: the external RAG router uses the field name `client_id`, but in this
    Django project that identifier corresponds to a Business. We accept
    `business_id` here and forward it as `client_id` to the RAG endpoint.

    The RAG endpoint expects form fields: client_id, agent_id, token_auth, file, file_name.
    """
    base = getattr(settings, "RAG_API_URL", "http://localhost:8001")
    url = f"{base.rstrip('/')}/api/v1/document/upload"
    data = {
        # forward business_id using the field name the RAG expects
        "client_id": str(business_id),
        "agent_id": str(agent_id),
        "token_auth": token_auth or getattr(settings, "RAG_CLIENT_TOKEN", ""),
        "file_name": file_name,
    }

    with open(file_path, "rb") as fh:
        files = {"file": (file_name, fh, content_type or "application/octet-stream")}
        resp = requests.post(url, data=data, files=files, timeout=getattr(settings, "RAG_TIMEOUT", 30))
    resp.raise_for_status()
    return resp.json()


def chat_with_agent(*, agent_id: int, prompt: str, message: str, top_k: int = 5):
    base = getattr(settings, "RAG_API_URL", "http://localhost:8001")
    url = f"{base.rstrip('/')}/api/v1/messages"
    payload = {
        "agent_id": str(agent_id),
        "prompt": prompt,
        "message": message,
        "top_k": top_k,
    }
    resp = requests.post(url, json=payload, timeout=getattr(settings, "RAG_TIMEOUT", 30))
    resp.raise_for_status()
    return resp.json()