"""Proveedores de dependencias inyectables (FastAPI Depends)."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import Depends, Header, HTTPException, Query, Request
from fastapi import status as estado_http
from langgraph.graph.state import CompiledStateGraph
from psycopg_pool import ConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.reglas import normalizar_session_id
from src.agentes.runtime_agente import RuntimeAgenteBundle
from src.api.configuracion import obtener_configuracion
from src.api.factoria_grafo_agente import construir_grafo_agente_produccion_o_none
from src.persistencia.modelos import Usuario
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.repositorios.usuarios import RepositorioUsuarios
from src.api.servicios.agente_m2_config import ServicioAgenteM2Config

# Nombres canonicos del mecanismo de sesion (Modulo 2); ver README seccion API de sesion.
NOMBRE_COOKIE_SESION = "fvl_session_id"
NOMBRE_HEADER_SESION = "X-Session-Id"


async def obtener_grafo_agente(request: Request) -> CompiledStateGraph:
    """
    Retorna el grafo LangGraph compilado del agente (cache en ``app.state``).

    Si el arranque dejo ``grafo_agente`` en ``None`` (p. ej. OpenAI no disponible al boot),
    intenta recompilar una vez bajo candado async.
    """
    grafo = getattr(request.app.state, "grafo_agente", None)
    if grafo is not None:
        return grafo  # type: ignore[no-any-return]

    lock = getattr(request.app.state, "_lock_grafo_agente", None)
    if lock is None:
        lock = asyncio.Lock()
        request.app.state._lock_grafo_agente = lock

    cfg = obtener_configuracion()
    async with lock:
        grafo = getattr(request.app.state, "grafo_agente", None)
        if grafo is not None:
            return grafo  # type: ignore[no-any-return]
        nuevo = construir_grafo_agente_produccion_o_none(cfg)
        if nuevo is None:
            raise HTTPException(
                status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "El agente conversacional no esta disponible. Verifique OPENAI_API_KEY, "
                    "meta-prompt del router y conectividad a Qdrant segun la configuracion."
                ),
            )
        request.app.state.grafo_agente = nuevo
        return nuevo


async def obtener_bundle_runtime_agente(
    sesion: AsyncSession = Depends(obtener_sesion_db),
) -> RuntimeAgenteBundle:
    """
    Construye el snapshot de LLMs y prompts para la peticion actual (hot-reload desde PostgreSQL).
    """
    try:
        return await ServicioAgenteM2Config(sesion).construir_bundle_tiempo_ejecucion()
    except ValueError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def obtener_pool_memoria_psycopg(request: Request) -> ConnectionPool:
    """Pool sincrono compartido (``psycopg_pool``) para memoria LangChain."""
    pool = getattr(request.app.state, "psycopg_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pool de PostgreSQL para memoria conversacional no inicializado.",
        )
    return pool  # type: ignore[no-any-return]


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
        uuid_txt = normalizar_session_id(crudo.strip())
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
    "obtener_bundle_runtime_agente",
    "obtener_grafo_agente",
    "obtener_pool_memoria_psycopg",
    "obtener_sesion_db",
    "obtener_usuario_actual",
]
