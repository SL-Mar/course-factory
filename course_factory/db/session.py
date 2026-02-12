"""Database engine and session management."""
from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from course_factory.db.models import Base

logger = logging.getLogger(__name__)


def get_engine(db_url: str) -> Engine:
    """Create a SQLAlchemy engine with connection-health checks.

    Args:
        db_url: Database connection URL (e.g. sqlite:///app.db).

    Returns:
        Configured SQLAlchemy Engine.
    """
    logger.debug("Creating database engine for %s", db_url.split("@")[-1])
    return create_engine(db_url, pool_pre_ping=True)


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    """Provide a transactional database session with automatic rollback.

    Usage::

        with get_session(engine) as session:
            session.add(obj)

    Args:
        engine: SQLAlchemy Engine to bind the session to.

    Yields:
        A scoped Session instance.
    """
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Session rolled back due to error")
        raise
    finally:
        session.close()


def init_db(db_url: str) -> Engine:
    """Create all tables defined in Base.metadata.

    Args:
        db_url: Database connection URL.

    Returns:
        The Engine used to create tables (useful for subsequent sessions).
    """
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")
    return engine
