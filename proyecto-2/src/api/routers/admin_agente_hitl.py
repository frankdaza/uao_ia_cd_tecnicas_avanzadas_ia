"""Rutas admin para configurar HITL en escalamiento clinico."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as estado_http

from src.agentes.estado_hitl import AgenteHitlEstado, AgenteHitlSnapshot
from src.api.dependencias import requerir_acceso_admin
from src.api.esquemas_agente_hitl import AgenteHitlConfigParche, AgenteHitlConfigVista

router = APIRouter(
    prefix="/admin",
    tags=["admin-agente-hitl"],
    dependencies=[Depends(requerir_acceso_admin)],
)


def _obtener_estado_hitl(request: Request) -> AgenteHitlEstado:
    estado = getattr(request.app.state, "agente_hitl", None)
    if estado is None:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La configuracion HITL del agente no esta inicializada.",
        )
    return estado


def _a_vista(snapshot: AgenteHitlSnapshot) -> AgenteHitlConfigVista:
    return AgenteHitlConfigVista(
        habilitado=snapshot.habilitado,
        updated_at=snapshot.updated_at,
    )


@router.get(
    "/agente-hitl",
    response_model=AgenteHitlConfigVista,
    summary="Obtener configuracion HITL del agente",
)
async def obtener_agente_hitl(
    estado_hitl: Annotated[AgenteHitlEstado, Depends(_obtener_estado_hitl)],
) -> AgenteHitlConfigVista:
    return _a_vista(await estado_hitl.leer())


@router.patch(
    "/agente-hitl",
    response_model=AgenteHitlConfigVista,
    summary="Actualizar configuracion HITL del agente (hot-reload)",
)
async def parchear_agente_hitl(
    cuerpo: AgenteHitlConfigParche,
    request: Request,
    estado_hitl: Annotated[AgenteHitlEstado, Depends(_obtener_estado_hitl)],
) -> AgenteHitlConfigVista:
    snapshot = await estado_hitl.aplicar(
        request.app.state.session_factory,
        habilitado=cuerpo.habilitado,
    )
    return _a_vista(snapshot)
