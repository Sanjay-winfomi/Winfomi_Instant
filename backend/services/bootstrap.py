"""Dev-friendly first-run bootstrap - creates one COMPANY_ADMIN account from env vars
if the users table is still empty, so there's always a way to log into the company
portal without a manual SQL insert. No hardcoded credentials in code."""
from __future__ import annotations

from api.store import count_users, create_user
from core.config import get_settings
from core.logging import get_logger
from services.auth import hash_password

logger = get_logger(__name__)


def ensure_seed_admin() -> None:
    if count_users() > 0:
        return
    settings = get_settings()
    create_user(
        email=settings.seed_admin_email.strip().lower(),
        password_hash=hash_password(settings.seed_admin_password),
    )
    logger.info("Seeded initial COMPANY_ADMIN account (%s).", settings.seed_admin_email)
