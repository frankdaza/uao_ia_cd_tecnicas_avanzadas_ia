"""Rutas admin para configurar el job periodico de recordatorios (UC-MVP-04)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as estado_http

from src.api.dependencias import requerir_acceso_admin
from src.api.esquemas_recordatorios_job import (
    RecordatoriosJobConfigParche,
    RecordatoriosJobConfigVista,
)
from src.integracion.recordatorios.estado_job import (
    RecordatoriosJobEstado,
    RecordatoriosJobSnapshot,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin-recordatorios-job"],
    dependencies=[Depends(requerir_acceso_admin)],
)


def _obtener_estado_job(request: Request) -> RecordatoriosJobEstado:
    estado = getattr(request.app.state, "recordatorios_job", None)
    if estado is None:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El job de recordatorios no esta inicializado.",
        )
    return estado


def _a_vista(snapshot: RecordatoriosJobSnapshot) -> RecordatoriosJobConfigVista:
    return RecordatoriosJobConfigVista(
        habilitado=snapshot.habilitado,
        interval_seg=snapshot.interval_seg,
        updated_at=snapshot.updated_at,
    )


@router.get(
    "/recordatorios-job",
    response_model=RecordatoriosJobConfigVista,
    summary="Obtener configuracion del job de recordatorios",
)
async def obtener_recordatorios_job(
    estado_job: Annotated[RecordatoriosJobEstado, Depends(_obtener_estado_job)],
) -> RecordatoriosJobConfigVista:
    return _a_vista(await estado_job.leer())


@router.patch(
    "/recordatorios-job",
    response_model=RecordatoriosJobConfigVista,
    summary="Actualizar configuracion del job de recordatorios (hot-reload)",
)
async def parchear_recordatorios_job(
    cuerpo: RecordatoriosJobConfigParche,
    request: Request,
    estado_job: Annotated[RecordatoriosJobEstado, Depends(_obtener_estado_job)],
) -> RecordatoriosJobConfigVista:
    datos = cuerpo.model_dump(exclude_unset=True)
    if not datos:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe enviar al menos un campo (habilitado o interval_seg).",
        )
    snapshot = await estado_job.aplicar(
        request.app.state.session_factory,
        habilitado=datos.get("habilitado"),
        interval_seg=datos.get("interval_seg"),
    )
    return _a_vista(snapshot)
