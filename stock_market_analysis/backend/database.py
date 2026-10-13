"""
QuantNova AI - Database Session & Engine Configuration
SQLAlchemy 2.0 engine, scoped session factory, and FastAPI dependency.
Resilient against offline or missing database driver during development.
"""

import logging
from typing import Generator, Optional, Any
from config import settings

logger = logging.getLogger("quantnova.database")

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import declarative_base, sessionmaker, Session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    declarative_base = lambda: object
    Session = None
    logger.warning("SQLAlchemy is not installed. Database persistence will be disabled.")

Base = declarative_base()

# Initialize Engine if SQLAlchemy is available
engine = None
SessionLocal = None

if SQLALCHEMY_AVAILABLE:
    db_url = settings.cleaned_database_url
    engine_kwargs = {
        "echo": False,
        "pool_pre_ping": True,  # Verifies connection liveness before checkout
    }

    if "sqlite" not in db_url:
        engine_kwargs.update({
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
        })

    try:
        engine = create_engine(db_url, **engine_kwargs)
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False,
        )
    except Exception as exc:
        logger.warning("Failed to initialize SQLAlchemy engine: %s", exc)
        engine = None
        SessionLocal = None


def get_db() -> Generator[Optional[Any], None, None]:
    """
    FastAPI Dependency yielding a database session.
    Gracefully yields None if database is unconfigured or driver is missing.
    """
    if not SQLALCHEMY_AVAILABLE or SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Utility to verify database connectivity.
    Returns True if database ping succeeds, False otherwise.
    """
    if not SQLALCHEMY_AVAILABLE or engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)
        return False
