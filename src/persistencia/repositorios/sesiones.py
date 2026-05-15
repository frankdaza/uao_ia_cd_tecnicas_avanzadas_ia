"""Helpers de sesion de memoria conversacional (LangChain Postgres)."""

from __future__ import annotations

import uuid


def sesion_id_memoria_langchain(usuario_id: uuid.UUID) -> str:
    """
    Identificador estable de sesion para ``PostgresChatMessageHistory``.

    Formato canonico acordado con LangChain: ``user:{uuid}`` (UUID en forma
    estandar con guiones). Debe permanecer estable entre reinicios para que el
    historial del usuario se recupere de PostgreSQL.
    """
    return f"user:{usuario_id}"
