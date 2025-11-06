import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

from app.core.domain.ports.llm_port import LLMPort


class OpenAILLMAdapter(LLMPort):
	def __init__(self, model: str = "gpt-4.1-mini") -> None:
		api_key = os.environ.get("OPENAI_API_KEY")
		if not api_key:
			raise ValueError("OPENAI_API_KEY debe estar configurado en las variables de entorno")
		base_url = os.environ.get("OPENAI_BASE_URL")
		self._client = OpenAI(api_key=api_key, base_url=base_url)
		self._model = model

	@staticmethod
	def _format_context(context: List[Dict[str, Any]]) -> str:
		"""
		Convierte el contexto de la búsqueda vectorial en un texto concatenado.
		Espera items con payload que puede incluir 'text' o 'text_preview'.
		"""
		parts: List[str] = []
		for item in context:
			payload = item.get("payload", {}) if isinstance(item, dict) else {}
			text = payload.get("text") or payload.get("text_preview")
			if text:
				parts.append(str(text))
		return "\n\n".join(parts)

	def response(self, prompt: str, context: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> str:
		ctx_text = self._format_context(context)
		base_system = (
			"Responde de forma clara y concisa. Usa únicamente el siguiente contexto si es relevante."
			" Si el contexto no contiene la información, dilo explícitamente y evita inventar datos."
		)
		system = f"{system_prompt}\n\n{base_system}" if system_prompt else base_system
		user_text = f"Pregunta: {prompt}\n\nContexto:\n{ctx_text}"

		resp = self._client.responses.create(
			model=self._model,
			input=[
				{"role": "system", "content": system},
				{"role": "user", "content": user_text},
			],
		)

		# Extraer texto (compatibilidad con SDKs)
		text = getattr(resp, "output_text", None)
		if text:
			return text
		# Fallback por si la estructura es distinta
		output = getattr(resp, "output", None)
		if isinstance(output, list):
			buff = []
			for item in output:
				if isinstance(item, dict) and item.get("type") == "message":
					for c in item.get("content", []):
						if c.get("type") == "output_text":
							buff.append(c.get("text", ""))
			if buff:
				return "".join(buff)
		# Si todo falla, devolver repr
		return str(resp)
