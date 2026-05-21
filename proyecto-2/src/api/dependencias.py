"""Dependencias FastAPI compartidas (auth admin, sesion DB, agente)."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from fastapi import status as estado_http
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import obtener_configuracion


async def obtener_session_factory_app(
    request: Request,
) -> async_sessionmaker[AsyncSession]:
    """Factoria de sesiones SQLAlchemy creada en el lifespan."""
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no inicializada.",
        )
    return factory


async def obtener_checkpointer_app(request: Request) -> BaseCheckpointSaver:
    """Checkpointer LangGraph (MemorySaver en tests SQLite)."""
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if checkpointer is None:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memoria del agente no inicializada.",
        )
    return checkpointer


async def requerir_clave_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> None:
    """Rechaza peticiones sin clave admin valida (patron M2 / TASK-64)."""
    cfg = obtener_configuracion()
    esperada = (cfg.admin_api_key or "").strip()
    if not esperada:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "La administracion remota esta deshabilitada: defina la variable de entorno "
                "ADMIN_API_KEY en el servidor."
            ),
        )
    recibida = (x_admin_key or "").strip()
    if len(recibida) != len(esperada):
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Credencial de administracion invalida o ausente.",
        )
    if not secrets.compare_digest(recibida, esperada):
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Credencial de administracion invalida o ausente.",
        )


async def requerir_clave_staff(
    x_staff_key: Annotated[str | None, Header(alias="X-Staff-Key")] = None,
) -> None:
    """Rechaza peticiones staff sin clave valida (MVP hasta TASK-105 JWT)."""
    cfg = obtener_configuracion()
    esperada = (cfg.staff_api_key or "").strip()
    if not esperada:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "La API staff esta deshabilitada: defina la variable de entorno "
                "STAFF_API_KEY en el servidor."
            ),
        )
    recibida = (x_staff_key or "").strip()
    if len(recibida) != len(esperada):
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Credencial de staff invalida o ausente.",
        )
    if not secrets.compare_digest(recibida, esperada):
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Credencial de staff invalida o ausente.",
        )


async def requerir_secreto_telegram(
    x_telegram_bot_api_secret_token: Annotated[
        str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")
    ] = None,
) -> None:
    """Valida el secret del webhook/integracion Telegram (TASK-106)."""
    cfg = obtener_configuracion()
    esperado = (cfg.telegram_webhook_secret or "").strip()
    if not esperado:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Integracion Telegram deshabilitada: defina TELEGRAM_WEBHOOK_SECRET."
            ),
        )
    recibido = (x_telegram_bot_api_secret_token or "").strip()
    if len(recibido) != len(esperado):
        raise HTTPException(
            status_code=estado_http.HTTP_403_FORBIDDEN,
            detail="Secret de Telegram invalido o ausente.",
        )
    if not secrets.compare_digest(recibido, esperado):
        raise HTTPException(
            status_code=estado_http.HTTP_403_FORBIDDEN,
            detail="Secret de Telegram invalido o ausente.",
        )
