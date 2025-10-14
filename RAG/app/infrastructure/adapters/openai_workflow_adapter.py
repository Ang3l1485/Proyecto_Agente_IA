from __future__ import annotations
from typing import Any, Dict, List
# El puerto del workflow
from app.core.domain.ports.workflowport import WorkflowPort
# Traigo las variables de entorno del sistema
from app.infrastructure.config.settings import Settings
from dataclasses import dataclass

# SDK del flujo de OpenAI (basado en tu snippet)
from agents import FileSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig
from openai.types.shared.reasoning import Reasoning
from pydantic import BaseModel


#Creo una estructura de respuesta que se va a devolver al dominio, permitiendo cambiar el adaptador a cualquier proveedor que yo desee.
@dataclass
class WorkflowResult:
    answer: str
    sources: List[str]
    meta: Dict[str, Any]

#Defino el adaptador cuyos atributos son las variables de entorno que no vienen del dominio y las herramientas y agentes que definen el flujo.
#El adaptador implementa el puerto del workflow
class OpenAIWorkflowAdapter(WorkflowPort):
    def __init__(self,settings: Settings) -> None:
        self._api_key = settings.OPENAI_API_KEY
        self._pre_model = settings.OPENAI_MODEL_PRE
        self._ans_model = settings.OPENAI_MODEL_ANS
        self._project_id = settings.OPENAI_PROJECT_ID
        self._base_url = settings.OPENAI_BASE_URL

        self._file_search = FileSearchTool(vector_store_ids=[
            "vs_68e6b2947b408191939d876d0384b849"
        ])

        self._pre_procesador = Agent(
            name="Pre-procesador",
            #  Instrucciones tal cual tu snippet — son parte de la “política” del agente
            instructions=(
                "Eres parte de un flujo y tu trabajo es mejorar la pregunta o texto que el usuario te va a entregar y deberás:\n"
                "1.  Solucionar cualquier error de ortografía que identifiques\n"
                "2. Mejorar la cohesión y coherencia del mensaje para que el próximo agente lo entienda mejor\n"
                "3. Quitar datos que consideres innecesarios o que no ayuden a la solución de la pregunta \n"
                "4. Agregar signos de puntuación si es necesario para mejorar el texto\n"
                "5. Si no tienes claro lo que trata de decir la persona, entonces no modifiques la estructura del texto, solo corrige la ortografía\n"
                "6. si el mensaje es muy largo, reduźcelo sin perder la lógica ni la intención de la pregunta."
            ),
            model=self._pre_model,
            model_settings=ModelSettings(
                store=True,
                reasoning=Reasoning(effort="low")
            )
        )

        self._respuesta = Agent(
            name="Respuesta",
            #  Instrucciones del agente “Respuesta” integradas
            instructions=(
                "Eres un agente de atención al cliente y tu misión es atender las necesidades del cliente.\n\n"
                "1. Saludarás amablemente y hablarás siempre en un tono claro, profesional y amigable.\n"
                "2. Solucionarás las necesidades del cliente, siempre con base a la información que buscarás en la base de datos vectorial tránsito de Medellín.\n"
                "3. No inventes información, sólo responde con base a la información que se te entrega de la base vectorial.\n"
                "4. Asegúrate de que el cliente se sienta satisfecho con tu respuesta.\n"
                "Contexto:\n"
                "Eres un agente de atención al cliente del tránsito de Medellín, te llamas Tomi y tu trabajo es responder a las dudas que tenga el usuario.\n"
                "Si la pregunta es relacionada con el tránsito de Medellín, busca la información relevante y responde sin cambiarla."
            ),
            model=self._ans_model,
            tools=[self._file_search],  # (ES) Aquí conectamos la herramienta de búsqueda vectorial
            model_settings=ModelSettings(
                store=True,
                reasoning=Reasoning(effort="low")
            )
        )
        # Metadatos del flujo para rastreo y auditoría
        self._run_config = RunConfig(trace_metadata={
            "__trace_source__": "agent-builder",
            "workflow_id": "wf_68e7e68fc9c48190aadd1ab409e152a30e1cf56003d6d00c"
        })

    async def run(self, input_text: str) -> Dict[str, Any]:
        """
        (ES) Ejecuta el flujo completo:
        - Pasa el input del usuario al preprocesador
        - Usa el texto mejorado como input para el agente de respuesta
        - Devuelve una salida estable (answer/sources/meta)
        """

        # (ES) 1) Item del usuario inicial
        user_item: TResponseInputItem = {
            "role": "user",
            "content": [{"type": "input_text", "text": input_text}],
        }

        # -----------------------------
        # Patrón A: usar texto mejorado
        # -----------------------------
        pre_temp = await Runner.run(
            self._pre_procesador,
            input=[user_item],          
            run_config=self._run_config,
        )
        improved_text = pre_temp.final_output_as(str)

        improved_user_item: TResponseInputItem = {
            "role": "user",
            "content": [{"type": "input_text", "text": improved_text}],
        }

        ans_temp = await Runner.run(
            self._respuesta,
            input=[improved_user_item],  
            run_config=self._run_config,
        )

        result = WorkflowResult(
            answer=ans_temp.final_output_as(str),
            sources=[],  # (ES) mapear si el SDK expone fuentes explícitas
            meta={
                "pre_items": len(pre_temp.new_items),
                "ans_items": len(ans_temp.new_items),
            },
        )

        # (ES) El puerto puede definir dict o dataclass. Aquí devuelvo dict por compatibilidad con tu firma actual.
        return {"answer": result.answer, "sources": result.sources, "meta": result.meta}