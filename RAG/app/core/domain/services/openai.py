from agents import FileSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig
from openai.types.shared.reasoning import Reasoning
from pydantic import BaseModel

# Tool definitions
file_search = FileSearchTool(
  vector_store_ids=[
    "vs_68e6b2947b408191939d876d0384b849"
  ]
)
pre_procesador = Agent(
  name="Pre-procesador",
  instructions="""Eres parte de un flujo y tu trabajo es mejorar la pregunta o texto que el usuario te va a entregar y deberás:
1.  Solucionar cualquier error de ortografía que identifiques
2. Mejorar la cohesión y coherencia del mensaje para que el próximo agente lo entienda mejor
3. Quitar datos que consideres innecesarios o que no ayuden a la solución de la pregunta 
4. Agregar signos de puntuación si es necesario para mejorar el texto
5. Si no tienes claro lo que trata de decir la persona, entonces no modifiques la estructura del texto, solo corrige la ortografía
6. si el mensaje es muy largo, reduźcelo sin perder la lógica ni la intención de la pregunta.""",
  model="gpt-5-nano",
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low"
    )
  )
)


respuesta = Agent(
  name="Respuesta",
  instructions="""Eres un agente de atención al cliente y tu misión es atender las necesidades del cliente.

1. Saludarás amablemente y hablarás siempre en un tono claro, profesional y amigable.
2. Solucionarás las necesidades del cliente, siempre con base a la información que buscarás en la base de datos vectorial tránsito de Medellín.
3. No inventes información, sólo responde con base a la información que se te entrega de la base vectorial.
4. Asegúrate de que el cliente se sienta satisfecho con tu respuesta.
Contexto:
Eres un agente de atención al cliente del tránsito de Medellín, te llamas Tomi y tu trabajo es responder a las dudas que tenga el usuario.
Si la pregunta es relacionada con el tránsito de Medellín, busca la información relevante y responde sin cambiarla.""",
  model="gpt-5-nano",
  tools=[
    file_search
  ],
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low"
    )
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  state = {

  }
  workflow = workflow_input.model_dump()
  conversation_history: list[TResponseInputItem] = [
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": workflow["input_as_text"]
        }
      ]
    }
  ]
  pre_procesador_result_temp = await Runner.run(
    pre_procesador,
    input=[

    ],
    run_config=RunConfig(trace_metadata={
      "__trace_source__": "agent-builder",
      "workflow_id": "wf_68e7e68fc9c48190aadd1ab409e152a30e1cf56003d6d00c"
    })
  )

  conversation_history.extend([item.to_input_item() for item in pre_procesador_result_temp.new_items])

  pre_procesador_result = {
    "output_text": pre_procesador_result_temp.final_output_as(str)
  }
  respuesta_result_temp = await Runner.run(
    respuesta,
    input=[
      *conversation_history
    ],
    run_config=RunConfig(trace_metadata={
      "__trace_source__": "agent-builder",
      "workflow_id": "wf_68e7e68fc9c48190aadd1ab409e152a30e1cf56003d6d00c"
    })
  )

  conversation_history.extend([item.to_input_item() for item in respuesta_result_temp.new_items])

  respuesta_result = {
    "output_text": respuesta_result_temp.final_output_as(str)
  }
  return respuesta_result
