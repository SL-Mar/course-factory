"""Text chunking utilities for the knowledge ingestion pipeline."""

from __future__ import annotations


class Chunker:
    """Split long documents into token-bounded chunks.

    Subclass and override :meth:`chunk` to implement a specific
    splitting strategy (recursive, sentence-aware, semantic, etc.).
    """

    def chunk(self, text: str, max_tokens: int = 512) -> list[str]:
        """Split *text* into chunks of at most *max_tokens* tokens.

        Args:
            text: The source text to split.
            max_tokens: Upper bound on tokens per chunk.

        Returns:
            A list of text chunks.

        Raises:
            NotImplementedError: Until a concrete strategy is wired in.
        """
        raise NotImplementedError("Chunker.chunk() not yet implemented")
