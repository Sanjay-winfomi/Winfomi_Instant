"""PostgreSQL engine + session factory. DATABASE_URL is the only thing that ever
changes to point this at a different Postgres instance - no code elsewhere depends
on connection details."""
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db_session() -> Session:
    return get_session_factory()()
