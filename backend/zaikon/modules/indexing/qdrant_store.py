"""Local Qdrant vector store adapter for the indexing module."""

from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from zaikon.core.config import settings


class QdrantVectorStore:
    """Small wrapper around QdrantClient.

    If `url` is provided, the client connects to a Qdrant server. Otherwise it
    uses embedded local storage at `path`, matching the PDF2GPU development
    setup.
    """

    def __init__(self, path: Path | str | None = None, url: str | None = None):
        self.path = Path(path) if path is not None else settings.qdrant_path
        self.url = url

        if self.url:
            self.client = QdrantClient(url=self.url)
            return

        if self.path is None:
            raise ValueError("Local Qdrant path is required when url is not set.")

        self.path.mkdir(parents=True, exist_ok=True)
        self.client = QdrantClient(path=str(self.path))

    @classmethod
    def from_settings(cls) -> "QdrantVectorStore":
        """Create the default local Qdrant store for this project."""

        return cls(path=settings.qdrant_path)

    def collection_exists(self, collection_name: str) -> bool:
        collections = self.client.get_collections().collections
        return any(collection.name == collection_name for collection in collections)

    def ensure_collection(
        self,
        collection_name: str,
        vector_size: int | None = None,
        distance: Distance = Distance.COSINE,
    ) -> None:
        if self.collection_exists(collection_name):
            return

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size or settings.embedding_dimensions,
                distance=distance,
            ),
        )

    def upsert_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        ids: list[int | str],
    ) -> None:
        if not (len(vectors) == len(payloads) == len(ids)):
            raise ValueError("vectors, payloads, and ids must have the same length.")

        points = [
            PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        result = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )
        return [
            {"id": point.id, "score": point.score, "payload": point.payload}
            for point in result.points
        ]
