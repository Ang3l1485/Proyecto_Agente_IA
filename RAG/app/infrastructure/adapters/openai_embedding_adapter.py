# app/infrastructure/adapters/openai_embedding_adapter.py

import os
from typing import List
from openai import OpenAI

from app.core.domain.ports.embedding_port import EmbeddingPort


class OpenAIEmbeddingAdapter(EmbeddingPort):
    def __init__(self, model: str = "text-embedding-3-large") -> None:
        self.model = model
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY debe estar configurado en las variables de entorno")

        self.client = OpenAI(api_key=api_key)

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]
