from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .services.rag_client import ingest_document
from django.conf import settings
import logging
from .models import Agent, Prompt, Document
from client.models import Client
from django.views import View
from django.db import IntegrityError


class AgentIndexView(View):

    def get(self, request, conversation_id=None):
        clients = Client.objects.all().order_by("name")
        selected_client = None

        # allow filtering by client via ?client=<id>
        client_id = request.GET.get("client")
        if client_id:
            try:
                selected_client = Client.objects.get(pk=int(client_id))
            except (Client.DoesNotExist, ValueError):
                selected_client = None

        # By default, never show agents from other clients; if no client selected, show none
        agents = (
            Agent.objects.filter(client=selected_client).order_by("-updated_at")
            if selected_client
            else Agent.objects.none()
        )

        conversation = None
        messages = []

        if conversation_id:
            conversation = get_object_or_404(Agent, pk=conversation_id)
            # pin selected_client to the agent's client when viewing it
            if conversation.client:
                selected_client = conversation.client

        # Always constrain the list to the resolved selected_client (after pinning)
        agents = (
            Agent.objects.filter(client=selected_client).order_by("-updated_at")
            if selected_client
            else Agent.objects.none()
        )

        return render(
            request,
            "agent/agent.html",
            {
                "conversations": agents,
                "conversation": conversation,
                "messages": messages,
                "clients": clients,
                "selected_client": selected_client,
            },
        )

    def post(self, request, conversation_id=None):
        # Determine selected client context similar to GET
        selected_client = None
        client_id = request.GET.get("client")
        if client_id:
            try:
                selected_client = Client.objects.get(pk=int(client_id))
            except (Client.DoesNotExist, ValueError):
                selected_client = None

        conversation = get_object_or_404(Agent, pk=conversation_id) if conversation_id else None

        def unique_agent_name(client: Client, desired: str | None) -> str:
            base = (desired or "Agente").strip() or "Agente"
            name = base
            i = 2
            while Agent.objects.filter(client=client, name=name).exists():
                name = f"{base} {i}"
                i += 1
            return name

        # Crear nuevo agent con nombre
        if request.POST.get("start_new"):
            title = request.POST.get("new_title") or ""
            client_pk = request.POST.get("client_id")
            client = Client.objects.filter(pk=client_pk).first() if client_pk else selected_client
            if not client:
                return redirect(reverse("agent:index"))
            name = unique_agent_name(client, title)
            try:
                conv = Agent.objects.create(name=name, client=client)
            except IntegrityError:
                # Rare race: regenerate a unique name and retry once
                name = unique_agent_name(client, name)
                conv = Agent.objects.create(name=name, client=client)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        new_title = request.POST.get("new_title")
        if new_title:
            client_pk = request.POST.get("client_id")
            client = Client.objects.filter(pk=client_pk).first() if client_pk else selected_client
            if not client:
                return redirect(reverse("agent:index"))
            name = unique_agent_name(client, new_title)
            try:
                conv = Agent.objects.create(name=name, client=client)
            except IntegrityError:
                name = unique_agent_name(client, name)
                conv = Agent.objects.create(name=name, client=client)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        # No hay mensajes; si el cliente envía un prompt inicial, créalo
        prompt_text = request.POST.get("system_prompt")
        if prompt_text and conversation:
            Prompt.objects.create(agent=conversation, content=prompt_text, is_active=True)
            return redirect(reverse("agent:detail", args=[conversation.pk]))

        # Fallback: redirect to list/detail view
        if conversation:
            return redirect(reverse("agent:detail", args=[conversation.pk]))
        return redirect(reverse("agent:index"))


class AgentHomeView(View):
    """Landing view for /agent/ when no conversation is selected.

    Shows only the conversations list and a placeholder on the right.
    """

    def get(self, request):
        # allow quick creation from the home view via POST start_new
        clients = Client.objects.all().order_by("name")
        selected_client = None
        client_id = request.GET.get("client")
        if client_id:
            try:
                selected_client = Client.objects.get(pk=int(client_id))
            except (Client.DoesNotExist, ValueError):
                selected_client = None

        conversations = (
            Agent.objects.filter(client=selected_client).order_by("-updated_at")
            if selected_client
            else Agent.objects.none()
        )
        return render(
            request,
            "agent/agent.html",
            {
                "conversations": conversations,
                "conversation": None,
                "messages": [],
                "no_selection": True,
                "clients": clients,
                "selected_client": selected_client,
            },
        )

    def post(self, request):
        selected_client = None
        client_id = request.GET.get("client")
        if client_id:
            try:
                selected_client = Client.objects.get(pk=int(client_id))
            except (Client.DoesNotExist, ValueError):
                selected_client = None

        if request.POST.get("start_new"):
            title = request.POST.get("new_title") or ""
            client_pk = request.POST.get("client_id")
            client = Client.objects.filter(pk=client_pk).first() if client_pk else selected_client
            if not client:
                return redirect(reverse("agent:index"))
            # Generate a unique name per client to avoid IntegrityError
            base = (title or "Agente").strip() or "Agente"
            name = base
            i = 2
            while Agent.objects.filter(client=client, name=name).exists():
                name = f"{base} {i}"
                i += 1
            try:
                conv = Agent.objects.create(name=name, client=client)
            except IntegrityError:
                # Retry once with a new suffix in case of race
                name = f"{base} {i}"
                conv = Agent.objects.create(name=name, client=client)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        new_title = request.POST.get("new_title")
        if new_title:
            client_pk = request.POST.get("client_id")
            client = Client.objects.filter(pk=client_pk).first() if client_pk else selected_client
            if not client:
                return redirect(reverse("agent:index"))
            base = new_title.strip() or "Agente"
            name = base
            i = 2
            while Agent.objects.filter(client=client, name=name).exists():
                name = f"{base} {i}"
                i += 1
            try:
                conv = Agent.objects.create(name=name, client=client)
            except IntegrityError:
                name = f"{base} {i}"
                conv = Agent.objects.create(name=name, client=client)
            return redirect(reverse("agent:detail", args=[conv.pk]))

        return redirect(reverse("agent:index"))


class SavePromptView(View):
    def post(self, request, conversation_id: int):
        conversation = get_object_or_404(Agent, pk=conversation_id)
        prompt = request.POST.get("system_prompt", "")
        if prompt:
            # Update existing prompt if DB enforces a single prompt per agent; otherwise create.
            existing = Prompt.objects.filter(agent=conversation).order_by("-updated_at").first()
            if existing:
                existing.content = prompt
                existing.is_active = True
                existing.save(update_fields=["content", "is_active", "updated_at"])  # keep single row updated
            else:
                try:
                    Prompt.objects.create(agent=conversation, content=prompt, is_active=True)
                except Exception:
                    # Fallback in case of a DB unique constraint on agent: update the single existing row
                    try:
                        only = Prompt.objects.get(agent=conversation)
                        only.content = prompt
                        only.is_active = True
                        only.save(update_fields=["content", "is_active", "updated_at"])
                    except Prompt.DoesNotExist:
                        raise
        return redirect(reverse("agent:detail", args=[conversation.pk]))


class UploadToConversationView(View):
    def post(self, request, conversation_id: int):
        conversation = get_object_or_404(Agent, pk=conversation_id)
        uploaded = request.FILES.get("file")
        if uploaded:
            doc = Document.objects.create(
                agent=conversation,
                file=uploaded,
                original_name=getattr(uploaded, "name", ""),
                content_type=getattr(uploaded, "content_type", ""),
                size=getattr(uploaded, "size", 0),
                uploaded_by=request.user if request.user.is_authenticated else None,
            )

            # Try to send the uploaded file to the RAG service using the router_document.py endpoint.
            try:
                file_path = getattr(doc.file, "path", None)
                resp = None
                if file_path:
                    # Mensaje explícito a consola antes de enviar al RAG
                    try:
                        cid = str(conversation.client.pk) if conversation.client else ""
                        fname = doc.original_name or getattr(doc.file, "name", "")
                        print(f"[upload] Enviando a RAG: client_id={cid} agent_id={conversation.pk} file_name={fname} path={file_path}", flush=True)
                    except Exception:
                        pass

                    resp = ingest_document(
                        business_id=str(conversation.client.pk) if conversation.client else "",
                        agent_id=str(conversation.pk),
                        token_auth=getattr(settings, "RAG_CLIENT_TOKEN", None),
                        document_id=str(doc.pk),
                        file_path=file_path,
                        file_name=doc.original_name or getattr(doc.file, "name", ""),
                        content_type=doc.content_type,
                    )
                    try:
                        object_key = resp.get("object_key") if isinstance(resp, dict) else None
                        if object_key:
                            logging.info("Archivo subido a MinIO: object_key=%s", object_key)
                            print(f"[upload] MinIO object_key={object_key}", flush=True)
                        else:
                            logging.info("Documento encolado para procesamiento en RAG (sin object_key en respuesta)")
                            print("[upload] Documento encolado para procesamiento en RAG (sin object_key)", flush=True)
                    except Exception:
                        # Silencioso: si la respuesta no es un dict, ya quedó registrado en logs
                        pass
                else:
                    # Fallback: send the file object directly by writing to a temporary file
                    logging.warning("Document file has no local path, skipping RAG ingest")
                    print("[upload] Archivo sin ruta local; se omite envío a RAG", flush=True)

                logging.info("RAG ingest response: %s", resp)
            except Exception as exc:  # keep view resilient
                logging.exception("Failed to ingest document to RAG: %s", exc)

        return redirect(reverse("agent:detail", args=[conversation.pk]))
