"""Vector store interface for the knowledge ingestion pipeline."""

from __future__ import annotations


class VectorStore:
    """Async interface to a vector database.

    Subclass and override :meth:`upsert` and :meth:`search` to plug in
    a concrete backend (Qdrant, Pinecone, ChromaDB, etc.).
    """

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict] | None = None,
    ) -> None:
        """Insert or update vectors in the store.

        Args:
            ids: Unique identifiers for each vector.
            vectors: The embedding vectors to store.
            payloads: Optional metadata dicts attached to each vector.

        Raises:
            NotImplementedError: Until a concrete backend is wired in.
        """
        raise NotImplementedError("VectorStore.upsert() not yet implemented")

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[dict]:
        """Return the *top_k* nearest neighbours for *query_vector*.

        Args:
            query_vector: The embedding to search against.
            top_k: Number of results to return.

        Returns:
            A list of result dicts with at least id, score,
            and payload keys.

        Raises:
            NotImplementedError: Until a concrete backend is wired in.
        """
        raise NotImplementedError("VectorStore.search() not yet implemented")
