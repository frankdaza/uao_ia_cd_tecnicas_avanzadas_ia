"""Endpoint de health-check: GET /api/salud."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.esquemas import RespuestaSalud

router = APIRouter(tags=["salud"])


@router.get("/salud", response_model=RespuestaSalud)
async def verificar_salud() -> RespuestaSalud:
    """Verifica que el servidor está en funcionamiento."""
    return RespuestaSalud(estado="ok", version="1.0.0")
