from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from core.config import get_settings
from core.logging import configure_logging, get_logger
from database.init_db import init_db

configure_logging()
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
    except Exception as exc:
        logger.error(
            "Could not reach PostgreSQL at startup (%s). Demo sessions will fail to "
            "save until the database is reachable - check DATABASE_URL and that "
            "Postgres is running.",
            exc,
        )
    yield


app = FastAPI(title="Self-Serve Instant AI Agent Sandbox", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
