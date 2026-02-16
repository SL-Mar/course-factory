"""FastAPI dependency singletons."""

from __future__ import annotations

from localnotion.config.settings import Settings
from localnotion.core.store import PageStore
from localnotion.core.index import PageIndex
from localnotion.core.graph import KnowledgeGraph
from localnotion.core.vector import VectorIndex
from localnotion.ai.router import LLMRouter
from localnotion.tables.engine import TableEngine

_settings: Settings | None = None
_store: PageStore | None = None
_index: PageIndex | None = None
_graph: KnowledgeGraph | None = None
_vector: VectorIndex | None = None
_router: LLMRouter | None = None
_tables: TableEngine | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.load_yaml()
    return _settings


def get_store() -> PageStore:
    global _store
    if _store is None:
        _store = PageStore(get_settings().data_dir)
    return _store


def get_index() -> PageIndex:
    global _index
    if _index is None:
        _index = PageIndex(get_settings().data_dir)
    return _index


def get_graph() -> KnowledgeGraph:
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph(get_index())
    return _graph


def get_vector() -> VectorIndex:
    global _vector
    if _vector is None:
        s = get_settings()
        _vector = VectorIndex(qdrant_url=s.qdrant_url, ollama_url=s.ollama_url)
    return _vector


def get_llm_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter(get_settings())
    return _router


def get_tables() -> TableEngine:
    global _tables
    if _tables is None:
        _tables = TableEngine(get_settings().data_dir)
    return _tables


def reset_all() -> None:
    global _settings, _store, _index, _graph, _vector, _router, _tables
    _settings = _store = _index = _graph = _vector = _router = _tables = None
