from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.client_routes import router as client_router
from api.company_auth import router as company_auth_router
from api.company_routes import router as company_router
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
        from services.bootstrap import ensure_seed_admin

        ensure_seed_admin()
    except Exception as exc:
        logger.error(
            "Could not reach PostgreSQL at startup (%s). Demo sessions will fail to "
            "save until the database is reachable - check DATABASE_URL and that "
            "Postgres is running.",
            exc,
        )
    yield


app = FastAPI(title="Winfomi Instant AI Platform", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(client_router)
app.include_router(company_auth_router)
app.include_router(company_router)
