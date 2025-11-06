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
        Convierte el contexto en texto concatenado.
        Acepta payload con claves: 'text', 'content', 'page_content' o 'text_preview'.
        """
        parts: List[str] = []
        for item in context or []:
            payload = item.get("payload", {}) if isinstance(item, dict) else {}
            text = (
                payload.get("text")
                or payload.get("content")
                or payload.get("page_content")
                or payload.get("text_preview")
            )
            if text:
                parts.append(str(text))
        return "\n\n".join(parts)

    def response(self, prompt: str, context: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> str:
        ctx_text = self._format_context(context)
        print(f"[llm] response ctx_items={len(context or [])} ctx_chars={len(ctx_text)} prompt_len={len(prompt)} sys_len={len(system_prompt or '')}")
        base_system = (
            "Responde de forma clara y concisa. Usa únicamente el siguiente contexto si es relevante."
            " Si el contexto no contiene la información, dilo explícitamente y evita inventar datos."
        )
        system = f"{system_prompt}\n\n{base_system}" if system_prompt else base_system
        user_text = f"Pregunta: {prompt}\n\nContexto:\n{ctx_text}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ]
        print(f"[llm] sending messages={len(messages)} user_text_chars={len(user_text)}")
        resp = self._client.responses.create(model=self._model, input=messages)
        text = getattr(resp, "output_text", None)
        print(f"[llm] got response output_text_len={len(text) if isinstance(text,str) else 0}")
        return text if isinstance(text, str) and text else str(resp)

    def response_with_history(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        ctx_text = self._format_context(context or [])
        print(f"[llm] response_with_history history_len={len(history or [])} ctx_items={len(context or [])} ctx_chars={len(ctx_text)} prompt_len={len(prompt)} sys_len={len(system_prompt or '')}")
        base_system = (
            "Responde de forma clara y concisa. Usa únicamente el siguiente contexto si es relevante."
            " Si el contexto no contiene la información, dilo explícitamente y evita inventar datos."
        )
        system = f"{system_prompt}\n\n{base_system}" if system_prompt else base_system

        messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
        for m in history or []:
            role = m.get("role")
            content = m.get("content")
            if role and content:
                messages.append({"role": role, "content": content})

        user_text = f"Pregunta: {prompt}"
        if ctx_text:
            user_text += f"\n\nContexto:\n{ctx_text}"
        messages.append({"role": "user", "content": user_text})

        print(f"[llm] sending messages={len(messages)} user_text_chars={len(user_text)}")
        resp = self._client.responses.create(model=self._model, input=messages)
        text = getattr(resp, "output_text", None)
        print(f"[llm] got response output_text_len={len(text) if isinstance(text,str) else 0}")
        return text if isinstance(text, str) and text else str(resp)
