"""FastAPI application for LocalNotion."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from localnotion import __version__
from localnotion.api.routers.pages import router as pages_router
from localnotion.api.routers.tables import router as tables_router
from localnotion.api.routers.graph import router as graph_router
from localnotion.api.routers.ai import router as ai_router
from localnotion.api.routers.engines import router as engines_router
from localnotion.api.routers.imports import router as imports_router
from localnotion.api.routers.setup import router as setup_router
from localnotion.api.routers.assets import router as assets_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LocalNotion",
    version=__version__,
    description="Local-first knowledge operating system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(pages_router)
app.include_router(tables_router)
app.include_router(graph_router)
app.include_router(ai_router)
app.include_router(engines_router)
app.include_router(imports_router)
app.include_router(setup_router)
app.include_router(assets_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.on_event("startup")
async def startup() -> None:
    """Rebuild page index from disk on startup; seed if empty; auto-reindex vectors."""
    import asyncio
    from localnotion.api.deps import get_store, get_index, get_vector

    try:
        store = get_store()
        index = get_index()

        # Seed starter content if this is a fresh install
        from localnotion.core.seed import seed_if_empty
        seeded = seed_if_empty(store, index)
        if seeded:
            logger.info("Startup: seeded %d starter pages", seeded)

        # Rebuild index from all pages on disk
        pages = store.list_all()
        index.rebuild_from_pages(pages)
        logger.info("Startup: indexed %d pages from disk", len(pages))

        # Auto-reindex vectors if Qdrant collection is empty
        try:
            vector = get_vector()
            await vector.ensure_collection()
            import aiohttp
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"{vector.qdrant_url}/collections/{vector.COLLECTION}",
                    timeout=aiohttp.ClientTimeout(total=5),
                )
                if resp.status == 200:
                    data = await resp.json()
                    count = data.get("result", {}).get("points_count", 0)
                    if count == 0:
                        logger.info("Startup: Qdrant empty, launching background vector reindex for %d pages", len(pages))
                        from localnotion.api.routers.pages import _run_reindex
                        asyncio.create_task(_run_reindex())
                    else:
                        logger.info("Startup: Qdrant has %d points, skipping reindex", count)
        except Exception:
            logger.warning("Startup: vector reindex check failed", exc_info=True)

    except Exception:
        logger.warning("Startup indexing failed", exc_info=True)


# Static files — SPA fallback
_STATIC_DIR = Path(__file__).resolve().parent / "static"

if _STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        file_path = _STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_STATIC_DIR / "index.html")
