"""In-memory session store. MVP scope: sessions live for the process lifetime only
(documented limitation in README) - promoting this to SQLite/Postgres later is a
drop-in change since every access goes through this module."""
from __future__ import annotations

from threading import Lock

from schemas.session import DemoResult

_sessions: dict[str, DemoResult] = {}
_lock = Lock()


def save(result: DemoResult) -> None:
    with _lock:
        _sessions[result.session_id] = result


def get(session_id: str) -> DemoResult | None:
    with _lock:
        return _sessions.get(session_id)
