from typing import List, Dict, Any
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
        payloads: List[Dict[str, Any]],
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

    def search(self, vector: List[float], collection: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca los puntos más cercanos al vector en la colección indicada."""
        if not self.client.collection_exists(collection):
            return []

        results = self.client.search(
            collection_name=collection,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        parsed = []
        for p in results:
            parsed.append({
                "id": str(getattr(p, "id", "")),
                "score": float(getattr(p, "score", 0.0)),
                "payload": getattr(p, "payload", {}) or {},
            })
        return parsed