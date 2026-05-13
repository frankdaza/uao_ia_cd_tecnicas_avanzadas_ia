"""Proveedores de dependencias inyectables (FastAPI Depends)."""

from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, Query, Request
from fastapi import status as estado_http
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.memoria.historial import normalizar_session_id_postgres_langchain
from src.persistencia.modelos import Usuario
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.repositorios.usuarios import RepositorioUsuarios

# Nombres canonicos del mecanismo de sesion (Modulo 2); ver README seccion API de sesion.
NOMBRE_COOKIE_SESION = "fvl_session_id"
NOMBRE_HEADER_SESION = "X-Session-Id"


async def obtener_grafo_agente(request: Request) -> CompiledStateGraph:
    """Retorna el grafo LangGraph compilado del agente (singleton en ``app.state``)."""
    grafo = getattr(request.app.state, "grafo_agente", None)
    if grafo is None:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El agente conversacional no esta disponible. Verifique OPENAI_API_KEY, "
                "meta-prompt del router y conectividad a Qdrant segun la configuracion."
            ),
        )
    return grafo  # type: ignore[no-any-return]


async def obtener_usuario_actual(
    request: Request,
    sesion: AsyncSession = Depends(obtener_sesion_db),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    session_id: str | None = Query(default=None),
) -> Usuario:
    """
    Resuelve el usuario autenticado desde cabecera, query o cookie HTTP-only.

    Orden de precedencia: ``X-Session-Id`` > ``session_id`` (query) > cookie ``fvl_session_id``.
    El valor debe ser el ``session_id`` canonico (``user:{uuid}`` o UUID textual) alineado con
    la memoria LangChain Postgres (task-47).
    """
    crudo = x_session_id or session_id or request.cookies.get(NOMBRE_COOKIE_SESION)
    if not crudo or not crudo.strip():
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Sesion no indicada o invalida.",
        )
    try:
        uuid_txt = normalizar_session_id_postgres_langchain(crudo.strip())
        usuario_id = uuid.UUID(uuid_txt)
    except ValueError:
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Sesion no indicada o invalida.",
        ) from None

    repo = RepositorioUsuarios(sesion)
    usuario = await repo.obtener_por_id(usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Sesion no indicada o invalida.",
        )
    return usuario


__all__ = [
    "NOMBRE_COOKIE_SESION",
    "NOMBRE_HEADER_SESION",
    "obtener_grafo_agente",
    "obtener_sesion_db",
    "obtener_usuario_actual",
]
