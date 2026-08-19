"""Creates all tables if they don't already exist. Called once on API startup.
For an MVP sandbox, create_all() is the right amount of schema management - if this
grows into a product with evolving columns, swap this for Alembic migrations without
touching any other module (everything else talks to the DB through database/engine.py
and api/store.py only)."""
from core.logging import get_logger
from database.engine import get_engine
from database.models import Base

logger = get_logger(__name__)


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database tables ensured.")
