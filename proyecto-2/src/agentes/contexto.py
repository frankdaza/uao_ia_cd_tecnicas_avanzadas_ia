"""Contexto de runtime del agente (session_id y acceso a BD)."""

from __future__ import annotations

import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_PATRON_SESSION = re.compile(r"^telegram:(\d+)$")

_session_id: ContextVar[str | None] = ContextVar("taam_session_id", default=None)
_session_factory: ContextVar[async_sessionmaker[AsyncSession] | None] = ContextVar(
    "taam_session_factory",
    default=None,
)


class ContextoTaam(TypedDict, total=False):
    """Esquema de contexto pasado a ``create_agent`` (``context_schema``)."""

    session_id: str
    resumen_caso: str
    sin_vinculo: bool


@dataclass(frozen=True)
class SesionTelegram:
    """Identificador canonico ``telegram:{chat_id}``."""

    chat_id: int
    session_id: str


def establecer_contexto_runtime(
    *,
    session_id: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Fija contextvars para tools y middleware durante una invocacion."""
    _session_id.set(session_id)
    _session_factory.set(session_factory)


def limpiar_contexto_runtime() -> None:
    _session_id.set(None)
    _session_factory.set(None)


def obtener_session_id_runtime() -> str:
    sid = _session_id.get()
    if not sid:
        raise RuntimeError("session_id no establecido en contexto del agente.")
    return sid


def obtener_session_factory_runtime() -> async_sessionmaker[AsyncSession]:
    factory = _session_factory.get()
    if factory is None:
        raise RuntimeError("session_factory no establecido en contexto del agente.")
    return factory


def parsear_session_telegram(session_id: str) -> SesionTelegram | None:
    """Convierte ``telegram:123`` en chat_id; None si el formato no coincide."""
    m = _PATRON_SESSION.match(session_id.strip())
    if not m:
        return None
    chat_id = int(m.group(1))
    return SesionTelegram(chat_id=chat_id, session_id=f"telegram:{chat_id}")
