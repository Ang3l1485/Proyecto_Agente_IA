import os
import openai
from typing import List
from app.core.domain.ports.embedding_port import EmbeddingPort

class OpenAIEmbeddingAdapter(EmbeddingPort):
    def __init__(self, model: str = "text-embedding-3-large") -> None:
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.project_id = os.environ.get("OPENAI_PROJECT_ID")


        if not self.api_key or not self.project_id:
            raise ValueError("OPENAI_API_KEY Y OPENAI_PROJECT_ID DEBEN ESTAR CONFIGURADOS EN LAS VARIABLES DE ENTORNO")


        # Configurar la clave de API y el ID del proyecto de OpenAI
        openai.api_key = self.api_key
        openai.organization = self.project_id


    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
            # Crear embeddings utilizando la API de OpenAI
            response = openai.Embedding.create(
            input=texts,
            model=self.model
            )
            # Ordenar los embeddings por su índice original para mantener el orden
            sorted_embeddings = sorted(response["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_embeddings]