from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.domain.ports.workflowport import WorkflowPort
from app.infrastructure.config.settings import Settings

from openai import OpenAI
import anyio  # to run blocking client methods in a worker thread


@dataclass
class WorkflowResult:
    answer: str
    sources: List[str]
    meta: Dict[str, Any]


class OpenAIWorkflowAdapter(WorkflowPort):
    def __init__(self, settings: Settings) -> None:
        # === env/config ===
        self._api_key = settings.OPENAI_API_KEY
        self._base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"

        # modelos (puedes hardcodear aquí o usar fallback con .env)
        self._pre_model = settings.OPENAI_MODEL_PRE or "gpt-4.1-mini"
        self._ans_model = settings.OPENAI_MODEL_ANS or "gpt-4.1-mini"

        # si tienes un Workflow ID de OpenAI Workflows, también puedes usarlo en lugar de _ans_model
        self._workflow_id: Optional[str] = getattr(settings, "OPENAI_WORKFLOW_ID", None)

        # cliente
        self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)

        # prompt base (sacados de tus instrucciones originales)
        self._pre_instructions = (
            "Eres parte de un flujo y tu trabajo es mejorar la pregunta o texto que el usuario te va a entregar y deberás:\n"
            "1. Solucionar cualquier error de ortografía que identifiques\n"
            "2. Mejorar la cohesión y coherencia del mensaje para que el próximo agente lo entienda mejor\n"
            "3. Quitar datos que consideres innecesarios o que no ayuden a la solución de la pregunta\n"
            "4. Agregar signos de puntuación si es necesario para mejorar el texto\n"
            "5. Si no tienes claro lo que trata de decir la persona, no cambies la estructura; solo corrige ortografía\n"
            "6. Si el mensaje es muy largo, redúcelo sin perder la lógica ni la intención."
        )

        self._ans_instructions = (
            "Eres un agente de atención al cliente (Tomi) del tránsito de Medellín.\n"
            "1. Tono claro, profesional y amable.\n"
            "2. Responde con base en la base de conocimiento del tránsito de Medellín (no inventes).\n"
            "3. Asegúrate de que el cliente quede satisfecho.\n"
            "Si la pregunta es del tránsito de Medellín, responde sin alterar la información."
        )

    # -------- helpers internos (sincronía en hilo) ----------
    def _resp_sync(self, *, model: str, system: str | None, user_text: str):
        """
        Llama OpenAI Responses API de forma síncrona.
        """
        return self._client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system} if system else None,
                {"role": "user", "content": user_text},
            ],
        )

    async def _resp(self, *, model: str, system: str | None, user_text: str):
        return await anyio.to_thread.run_sync(
            self._resp_sync, model=model, system=system, user_text=user_text
        )

    @staticmethod
    def _extract_text(resp: Any) -> str:
        """
        Extrae texto de la Responses API (tolera estructuras).
        """
        # SDKs nuevos traen .output_text
        text = getattr(resp, "output_text", None)
        if text:
            return text

        # Fallback por si no existe
        text = ""
        output = getattr(resp, "output", None)
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict) and item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            text += c.get("text", "")
        return text

    # ----------------- puerto -----------------
    async def run(self, input_text: str) -> Dict[str, Any]:
        """
        Flujo:
        1) Pre-procesa el texto del usuario
        2) Usa el texto mejorado para responder (modelo final o workflow)
        """
        # 1) PREPROCESADOR
        pre_resp = await self._resp(
            model=self._pre_model,
            system=self._pre_instructions,
            user_text=input_text,
        )
        improved_text = self._extract_text(pre_resp) or input_text

        # 2) RESPUESTA (si tienes workflow_id, úsalo; si no, usa _ans_model)
        model_or_workflow = self._workflow_id or self._ans_model
        ans_resp = await self._resp(
            model=model_or_workflow,
            system=self._ans_instructions,
            user_text=improved_text,
        )
        answer = self._extract_text(ans_resp)

        result = WorkflowResult(
            answer=answer,
            sources=[],  # aquí puedes mapear citations si las agregas a la respuesta
            meta={
                "pre_model": self._pre_model,
                "ans_model_or_workflow": model_or_workflow,
                "pre_id": getattr(pre_resp, "id", None),
                "ans_id": getattr(ans_resp, "id", None),
            },
        )
        return {"answer": result.answer, "sources": result.sources, "meta": result.meta}




# from __future__ import annotations
# from typing import Any, Dict, List
# # El puerto del workflow
# from app.core.domain.ports.workflowport import WorkflowPort
# # Traigo las variables de entorno del sistema
# from app.infrastructure.config.settings import Settings
# from dataclasses import dataclass

# # SDK del flujo de OpenAI (basado en tu snippet)
# from agents import FileSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig
# from openai.types.shared.reasoning import Reasoning
# from pydantic import BaseModel


# #Creo una estructura de respuesta que se va a devolver al dominio, permitiendo cambiar el adaptador a cualquier proveedor que yo desee.
# @dataclass
# class WorkflowResult:
#     answer: str
#     sources: List[str]
#     meta: Dict[str, Any]

# #Defino el adaptador cuyos atributos son las variables de entorno que no vienen del dominio y las herramientas y agentes que definen el flujo.
# #El adaptador implementa el puerto del workflow
# class OpenAIWorkflowAdapter(WorkflowPort):
#     def __init__(self,settings: Settings) -> None:
#         self._api_key = settings.OPENAI_API_KEY
#         self._pre_model = settings.OPENAI_MODEL_PRE
#         self._ans_model = settings.OPENAI_MODEL_ANS
#         self._project_id = settings.OPENAI_PROJECT_ID
#         self._base_url = settings.OPENAI_BASE_URL

#         self._file_search = FileSearchTool(vector_store_ids=[
#             "vs_68e6b2947b408191939d876d0384b849"
#         ])

#         self._pre_procesador = Agent(
#             name="Pre-procesador",
#             #  Instrucciones tal cual tu snippet — son parte de la “política” del agente
#             instructions=(
#                 "Eres parte de un flujo y tu trabajo es mejorar la pregunta o texto que el usuario te va a entregar y deberás:\n"
#                 "1.  Solucionar cualquier error de ortografía que identifiques\n"
#                 "2. Mejorar la cohesión y coherencia del mensaje para que el próximo agente lo entienda mejor\n"
#                 "3. Quitar datos que consideres innecesarios o que no ayuden a la solución de la pregunta \n"
#                 "4. Agregar signos de puntuación si es necesario para mejorar el texto\n"
#                 "5. Si no tienes claro lo que trata de decir la persona, entonces no modifiques la estructura del texto, solo corrige la ortografía\n"
#                 "6. si el mensaje es muy largo, reduźcelo sin perder la lógica ni la intención de la pregunta."
#             ),
#             model=self._pre_model,
#             model_settings=ModelSettings(
#                 store=True,
#                 reasoning=Reasoning(effort="low")
#             )
#         )

#         self._respuesta = Agent(
#             name="Respuesta",
#             #  Instrucciones del agente “Respuesta” integradas
#             instructions=(
#                 "Eres un agente de atención al cliente y tu misión es atender las necesidades del cliente.\n\n"
#                 "1. Saludarás amablemente y hablarás siempre en un tono claro, profesional y amigable.\n"
#                 "2. Solucionarás las necesidades del cliente, siempre con base a la información que buscarás en la base de datos vectorial tránsito de Medellín.\n"
#                 "3. No inventes información, sólo responde con base a la información que se te entrega de la base vectorial.\n"
#                 "4. Asegúrate de que el cliente se sienta satisfecho con tu respuesta.\n"
#                 "Contexto:\n"
#                 "Eres un agente de atención al cliente del tránsito de Medellín, te llamas Tomi y tu trabajo es responder a las dudas que tenga el usuario.\n"
#                 "Si la pregunta es relacionada con el tránsito de Medellín, busca la información relevante y responde sin cambiarla."
#             ),
#             model=self._ans_model,
#             tools=[self._file_search],  # (ES) Aquí conectamos la herramienta de búsqueda vectorial
#             model_settings=ModelSettings(
#                 store=True,
#                 reasoning=Reasoning(effort="low")
#             )
#         )
#         # Metadatos del flujo para rastreo y auditoría
#         self._run_config = RunConfig(trace_metadata={
#             "__trace_source__": "agent-builder",
#             "workflow_id": "wf_68e7e68fc9c48190aadd1ab409e152a30e1cf56003d6d00c"
#         })

#     async def run(self, input_text: str) -> Dict[str, Any]:
#         """
#         (ES) Ejecuta el flujo completo:
#         - Pasa el input del usuario al preprocesador
#         - Usa el texto mejorado como input para el agente de respuesta
#         - Devuelve una salida estable (answer/sources/meta)
#         """

#         # (ES) 1) Item del usuario inicial
#         user_item: TResponseInputItem = {
#             "role": "user",
#             "content": [{"type": "input_text", "text": input_text}],
#         }

#         # -----------------------------
#         # Patrón A: usar texto mejorado
#         # -----------------------------
#         pre_temp = await Runner.run(
#             self._pre_procesador,
#             input=[user_item],          
#             run_config=self._run_config,
#         )
#         improved_text = pre_temp.final_output_as(str)

#         improved_user_item: TResponseInputItem = {
#             "role": "user",
#             "content": [{"type": "input_text", "text": improved_text}],
#         }

#         ans_temp = await Runner.run(
#             self._respuesta,
#             input=[improved_user_item],  
#             run_config=self._run_config,
#         )

#         result = WorkflowResult(
#             answer=ans_temp.final_output_as(str),
#             sources=[],  # (ES) mapear si el SDK expone fuentes explícitas
#             meta={
#                 "pre_items": len(pre_temp.new_items),
#                 "ans_items": len(ans_temp.new_items),
#             },
#         )

#         # (ES) El puerto puede definir dict o dataclass. Aquí devuelvo dict por compatibilidad con tu firma actual.
#         return {"answer": result.answer, "sources": result.sources, "meta": result.meta}

