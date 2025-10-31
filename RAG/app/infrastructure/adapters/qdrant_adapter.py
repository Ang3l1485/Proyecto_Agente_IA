# adapters/vector/qdrant_vector_adapter.py
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from app.core.domain.ports.vector_port import VectorPort


class QdrantVectorAdapter(VectorPort):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        grpc: bool = False,
        api_key: str | None = None,
    ) -> None:
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            prefer_grpc=grpc,
        )

    def up_embeddings(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[Dict],
        collection: str,
    ) -> None:
        # Verifica que la colección exista y tenga la dimensión adecuada
        if not self.client.collection_exists(collection):
            self.client.recreate_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=len(vectors[0]),
                    distance=Distance.COSINE,
                ),
            )

        points = [
            PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i])
            for i in range(len(ids))
        ]

        self.client.upsert(collection_name=collection, points=points)