"""Vector search via Qdrant + local embeddings via Ollama."""

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp

from localnotion.core.models import Page, SearchResult

logger = logging.getLogger(__name__)


class VectorIndex:
    """Manages vector embeddings for semantic search via Qdrant."""

    COLLECTION = "pages"
    EMBEDDING_MODEL = "nomic-embed-text"
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 64

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        ollama_url: str = "http://localhost:11434",
    ) -> None:
        self.qdrant_url = qdrant_url.rstrip("/")
        self.ollama_url = ollama_url.rstrip("/")
        self._initialized = False

    async def ensure_collection(self) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        if self._initialized:
            return
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"{self.qdrant_url}/collections/{self.COLLECTION}",
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                if resp.status == 200:
                    self._initialized = True
                    return

                await session.put(
                    f"{self.qdrant_url}/collections/{self.COLLECTION}",
                    json={
                        "vectors": {
                            "size": 768,
                            "distance": "Cosine",
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                self._initialized = True
                logger.info("Created Qdrant collection '%s'", self.COLLECTION)
        except Exception:
            logger.warning("Could not ensure Qdrant collection", exc_info=True)

    def chunk_markdown(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        if len(words) <= self.CHUNK_SIZE:
            return [text] if text.strip() else []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + self.CHUNK_SIZE, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP
        return chunks

    async def embed(self, text: str) -> list[float]:
        """Get embedding vector from Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{self.ollama_url}/api/embed",
                    json={"model": self.EMBEDDING_MODEL, "input": text},
                    timeout=aiohttp.ClientTimeout(total=60),
                )
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Ollama embed failed: %s", body)
                    return []
                data = await resp.json()
                embeddings = data.get("embeddings", [])
                return embeddings[0] if embeddings else []
        except Exception:
            logger.warning("Embedding failed", exc_info=True)
            return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        results = []
        for text in texts:
            vec = await self.embed(text)
            results.append(vec)
        return results

    async def index_page(self, page: Page) -> list[str]:
        """Chunk page content, embed, and store in Qdrant."""
        await self.ensure_collection()

        # Remove old points for this page first
        await self._delete_page_points(page.id)

        full_text = f"{page.title}\n\n{page.content}"
        chunks = self.chunk_markdown(full_text)
        if not chunks:
            return []

        embeddings = await self.embed_batch(chunks)

        import uuid

        point_ids: list[str] = []
        points: list[dict[str, Any]] = []

        for chunk, embedding in zip(chunks, embeddings):
            if not embedding:
                continue
            point_id = str(uuid.uuid4())
            points.append({
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "page_id": page.id,
                    "title": page.title,
                    "chunk_text": chunk[:500],
                    "tags": page.tags,
                    "type": page.type,
                    "workspace": page.workspace,
                },
            })
            point_ids.append(point_id)

        if points:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.put(
                        f"{self.qdrant_url}/collections/{self.COLLECTION}/points",
                        json={"points": points},
                        timeout=aiohttp.ClientTimeout(total=30),
                    )
            except Exception:
                logger.warning("Failed to upsert points to Qdrant", exc_info=True)

        return point_ids

    async def search(
        self,
        query: str,
        limit: int = 10,
        workspace: Optional[str] = None,
        page_type: Optional[str] = None,
    ) -> list[SearchResult]:
        """Semantic search across all pages."""
        await self.ensure_collection()

        query_vector = await self.embed(query)
        if not query_vector:
            return []

        body: dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
        }

        filters: list[dict] = []
        if workspace:
            filters.append({"key": "workspace", "match": {"value": workspace}})
        if page_type:
            filters.append({"key": "type", "match": {"value": page_type}})
        if filters:
            body["filter"] = {"must": filters}

        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{self.qdrant_url}/collections/{self.COLLECTION}/points/search",
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=15),
                )
                if resp.status != 200:
                    return []
                data = await resp.json()
                results = []
                for hit in data.get("result", []):
                    payload = hit.get("payload", {})
                    results.append(SearchResult(
                        page_id=payload.get("page_id", ""),
                        title=payload.get("title", ""),
                        chunk_text=payload.get("chunk_text", ""),
                        score=hit.get("score", 0.0),
                        tags=payload.get("tags", []),
                        page_type=payload.get("type", "page"),
                    ))
                return results
        except Exception:
            logger.warning("Qdrant search failed", exc_info=True)
            return []

    async def _delete_page_points(self, page_id: str) -> None:
        """Remove all vectors for a given page."""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.qdrant_url}/collections/{self.COLLECTION}/points/delete",
                    json={
                        "filter": {
                            "must": [{"key": "page_id", "match": {"value": page_id}}]
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                )
        except Exception:
            logger.debug("Could not delete old points for page %s", page_id)

    async def rebuild(self, pages: list[Page]) -> int:
        """Re-index all pages."""
        count = 0
        for page in pages:
            if not page.is_deleted:
                ids = await self.index_page(page)
                count += len(ids)
        logger.info("Re-indexed %d chunks from %d pages", count, len(pages))
        return count
