"""Dependencias FastAPI compartidas (auth admin, sesion DB)."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi import status as estado_http

from src.configuracion import obtener_configuracion


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
