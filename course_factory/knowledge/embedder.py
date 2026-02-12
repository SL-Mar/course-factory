"""Text embedding interface for the knowledge ingestion pipeline."""

from __future__ import annotations


class Embedder:
    """Async wrapper around an embedding model.

    Subclass and override :meth:`embed` to plug in a concrete provider
    (OpenAI, sentence-transformers, etc.).
    """

    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for *text*.

        Raises:
            NotImplementedError: Until a concrete provider is wired in.
        """
        raise NotImplementedError("Embedder.embed() not yet implemented")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of *texts*.

        The default implementation calls :meth:`embed` sequentially.
        Override for providers that support native batching.

        Raises:
            NotImplementedError: Delegates to :meth:`embed`.
        """
        return [await self.embed(t) for t in texts]
