from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .services.rag_client import ingest_document
from django.conf import settings
import logging
from .models import Agent, Prompt, Document
from business.models import Business
from django.views.decorators.http import require_POST


def agent_index(request, conversation_id=None):
    """Show list of conversations on the left and messages for the selected conversation on the right.

    POST behavior:
    - If `new_title` is present, create a new Conversation and redirect to it.
    - If `message` is present and a conversation is selected, create a Message in that conversation.
    """
    businesses = Business.objects.all().order_by("name")
    selected_business = None

    # allow filtering by business via ?biz=<id>
    biz_id = request.GET.get("biz")
    if biz_id:
        try:
            selected_business = Business.objects.get(pk=int(biz_id))
        except (Business.DoesNotExist, ValueError):
            selected_business = None

    if selected_business:
        agents = Agent.objects.filter(business=selected_business).order_by("-updated_at")
    else:
        agents = Agent.objects.order_by("-updated_at")
    conversation = None
    messages = []

    if conversation_id:
        conversation = get_object_or_404(Agent, pk=conversation_id)
        # pin selected_business to the agent's business when viewing it
        if conversation.business:
            selected_business = conversation.business

    if request.method == "POST":
        # Crear nuevo agent con nombre
        if request.POST.get("start_new"):
            title = request.POST.get("new_title") or ""
            biz_pk = request.POST.get("business_id")
            biz = Business.objects.filter(pk=biz_pk).first() if biz_pk else selected_business
            conv = Agent.objects.create(name=title or "Agente", business=biz)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        new_title = request.POST.get("new_title")
        if new_title:
            biz_pk = request.POST.get("business_id")
            biz = Business.objects.filter(pk=biz_pk).first() if biz_pk else selected_business
            conv = Agent.objects.create(name=new_title, business=biz)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        # No hay mensajes; si el cliente envía un prompt inicial, créalo
        prompt_text = request.POST.get("system_prompt")
        if prompt_text and conversation:
            Prompt.objects.create(agent=conversation, content=prompt_text, is_active=True)
            return redirect(reverse("agent:detail", args=[conversation.pk]))

    return render(
        request,
        "agent/agent.html",
        {
            "conversations": agents,
            "conversation": conversation,
            "messages": messages,
            "businesses": businesses,
            "selected_business": selected_business,
        },
    )


def agent_home(request):
    """Landing view for /agent/ when no conversation is selected.

    Shows only the conversations list on the left and a friendly placeholder on the right.
    """
    # allow quick creation from the home view via POST start_new
    businesses = Business.objects.all().order_by("name")
    selected_business = None
    biz_id = request.GET.get("biz")
    if biz_id:
        try:
            selected_business = Business.objects.get(pk=int(biz_id))
        except (Business.DoesNotExist, ValueError):
            selected_business = None

    if request.method == "POST":
        if request.POST.get("start_new"):
            title = request.POST.get("new_title") or ""
            biz_pk = request.POST.get("business_id")
            biz = Business.objects.filter(pk=biz_pk).first() if biz_pk else selected_business
            conv = Agent.objects.create(name=title or "Agente", business=biz)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        new_title = request.POST.get("new_title")
        if new_title:
            biz_pk = request.POST.get("business_id")
            biz = Business.objects.filter(pk=biz_pk).first() if biz_pk else selected_business
            conv = Agent.objects.create(name=new_title, business=biz)
            return redirect(reverse("agent:detail", args=[conv.pk]))

    conversations = Agent.objects.filter(business=selected_business) if selected_business else Agent.objects.order_by("-updated_at")
    return render(
        request,
        "agent/agent.html",
        {
            "conversations": conversations,
            "conversation": None,
            "messages": [],
            "no_selection": True,
            "businesses": businesses,
            "selected_business": selected_business,
        },
    )
from django.shortcuts import render

# Create your views here.


@require_POST
def save_prompt(request, conversation_id: int):
    conversation = get_object_or_404(Agent, pk=conversation_id)
    prompt = request.POST.get("system_prompt", "")
    if prompt:
        Prompt.objects.create(agent=conversation, content=prompt, is_active=True)
    return redirect(reverse("agent:detail", args=[conversation.pk]))


@require_POST
def upload_to_conversation(request, conversation_id: int):
    conversation = get_object_or_404(Agent, pk=conversation_id)
    uploaded = request.FILES.get("file")
    if uploaded:
        doc = Document.objects.create(
            agent=conversation,
            file=uploaded,
            original_name=getattr(uploaded, "name", ""),
            content_type=getattr(uploaded, "content_type", ""),
            size=getattr(uploaded, "size", 0),
        )

        # Try to send the uploaded file to the RAG service using the router_document.py endpoint.
        try:
            file_path = getattr(doc.file, "path", None)
            resp = None
            if file_path:
                resp = ingest_document(
                    business_id=str(conversation.business.pk) if conversation.business else "",
                    agent_id=str(conversation.pk),
                    token_auth=getattr(settings, "RAG_CLIENT_TOKEN", None),
                    document_id=str(doc.pk),
                    file_path=file_path,
                    file_name=doc.original_name or getattr(doc.file, "name", ""),
                    content_type=doc.content_type,
                )
            else:
                # Fallback: send the file object directly by writing to a temporary file
                logging.warning("Document file has no local path, skipping RAG ingest")

            logging.info("RAG ingest response: %s", resp)
        except Exception as exc:  # keep view resilient
            logging.exception("Failed to ingest document to RAG: %s", exc)

    return redirect(reverse("agent:detail", args=[conversation.pk]))
