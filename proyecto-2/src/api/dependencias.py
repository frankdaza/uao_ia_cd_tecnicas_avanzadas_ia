"""Dependencias FastAPI compartidas (auth admin, staff JWT, sesion DB, agente)."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi import status as estado_http
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.auth_staff import ClaimsStaffJwt, decodificar_token_staff
from src.configuracion import obtener_configuracion
from src.persistencia.modelos import UsuarioStaff
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.repositorios.usuarios_staff import RepositorioUsuariosStaff


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


def _extraer_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.strip():
        return None
    partes = authorization.strip().split(None, 1)
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return None
    token = partes[1].strip()
    return token or None


async def _claims_desde_bearer(authorization: str | None) -> ClaimsStaffJwt | None:
    token = _extraer_bearer(authorization)
    if not token:
        return None
    cfg = obtener_configuracion()
    if not (cfg.staff_jwt_secret or "").strip():
        return None
    try:
        return decodificar_token_staff(token, cfg)
    except (jwt.InvalidTokenError, ValueError):
        return None


async def obtener_staff_actual(
    authorization: Annotated[str | None, Header()] = None,
    sesion: AsyncSession = Depends(obtener_sesion_db),
) -> UsuarioStaff:
    """Resuelve el usuario staff desde JWT Bearer (TASK-105)."""
    cfg = obtener_configuracion()
    if not (cfg.staff_jwt_secret or "").strip():
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Autenticacion staff deshabilitada: defina STAFF_JWT_SECRET en el servidor."
            ),
        )

    token = _extraer_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion invalido o ausente.",
        )

    try:
        claims = decodificar_token_staff(token, cfg)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion expirado.",
        ) from None
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion invalido o ausente.",
        ) from None

    repo = RepositorioUsuariosStaff(sesion)
    usuario = await repo.obtener_por_id(claims.usuario_id)
    if usuario is None or usuario.rol != claims.rol:
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion invalido o ausente.",
        )
    return usuario


def requerir_rol_staff(*roles_permitidos: str) -> Callable[..., object]:
    """Factory: exige que ``obtener_staff_actual`` devuelva uno de los roles indicados."""

    async def _dependencia(
        usuario: Annotated[UsuarioStaff, Depends(obtener_staff_actual)],
    ) -> UsuarioStaff:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=estado_http.HTTP_403_FORBIDDEN,
                detail="Rol no autorizado para esta operacion.",
            )
        return usuario

    return _dependencia


async def requerir_acceso_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """
    Catalogo admin: ``X-Admin-Key`` valida **o** JWT Bearer con ``rol=admin``.

    Mantiene compatibilidad con integraciones que solo usan clave estatica.
    """
    claims = await _claims_desde_bearer(authorization)
    if claims is not None:
        if claims.rol == "admin":
            return
        raise HTTPException(
            status_code=estado_http.HTTP_403_FORBIDDEN,
            detail="Rol no autorizado para esta operacion.",
        )

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
