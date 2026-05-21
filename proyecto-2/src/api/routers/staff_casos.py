"""Rutas staff de casos postoperatorio (UC-MVP-02)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as estado_http
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencias import obtener_staff_actual
from src.api.esquemas_casos import (
    CasoVista,
    CodigoEmparejamientoRespuesta,
    CrearCasoCuerpo,
    ListadoCasosRespuesta,
)
from src.api.servicios.emparejamiento import (
    EmparejamientoError,
    caso_tiene_vinculo_telegram,
    codigo_pendiente_activo,
    generar_codigo_para_caso,
    validar_tipo_procedimiento_indexado,
)
from src.configuracion import obtener_configuracion
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.modelos import CasoPostoperatorio
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio

router = APIRouter(
    prefix="/staff",
    tags=["staff-casos"],
    dependencies=[Depends(obtener_staff_actual)],
)


async def _a_vista(sesion: AsyncSession, fila: CasoPostoperatorio) -> CasoVista:
    return CasoVista(
        id=fila.id,
        paciente_doc_id=fila.paciente_doc_id,
        paciente_nombre=fila.paciente_nombre,
        tipo_procedimiento_id=fila.tipo_procedimiento_id,
        cirujano_id=fila.cirujano_id,
        cirujano_nombre=fila.cirujano_nombre,
        fecha_cirugia=fila.fecha_cirugia,
        notas_especificas=fila.notas_especificas,
        estado=fila.estado,
        created_at=fila.created_at,
        vinculado_telegram=await caso_tiene_vinculo_telegram(sesion, fila),
        codigo_emparejamiento_activo=await codigo_pendiente_activo(sesion, fila.id),
    )


def _http_desde_emparejamiento(exc: EmparejamientoError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_http,
        detail={
            "error": exc.codigo_error,
            "mensaje": exc.mensaje_telegram,
        },
    )


@router.post(
    "/casos",
    response_model=CasoVista,
    status_code=estado_http.HTTP_201_CREATED,
)
async def crear_caso(
    cuerpo: CrearCasoCuerpo,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> CasoVista:
    try:
        await validar_tipo_procedimiento_indexado(sesion, cuerpo.tipo_procedimiento_id)
    except EmparejamientoError as exc:
        raise _http_desde_emparejamiento(exc) from exc

    repo = RepositorioCasosPostoperatorio(sesion)
    fila = await repo.crear(
        paciente_doc_id=cuerpo.paciente_doc_id,
        paciente_nombre=cuerpo.paciente_nombre,
        tipo_procedimiento_id=cuerpo.tipo_procedimiento_id,
        cirujano_id=cuerpo.cirujano_id,
        cirujano_nombre=cuerpo.cirujano_nombre,
        fecha_cirugia=cuerpo.fecha_cirugia,
        notas_especificas=cuerpo.notas_especificas,
        estado="activo",
    )
    return await _a_vista(sesion, fila)


@router.get("/casos", response_model=ListadoCasosRespuesta)
async def listar_casos(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    estado: Annotated[str | None, Query(pattern="^(activo|cerrado)$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListadoCasosRespuesta:
    repo = RepositorioCasosPostoperatorio(sesion)
    filas = await repo.listar(estado=estado, limite=limit, offset=offset)
    items = [await _a_vista(sesion, f) for f in filas]
    return ListadoCasosRespuesta(items=items, limit=limit, offset=offset)


@router.post(
    "/casos/{caso_id}/codigo-emparejamiento",
    response_model=CodigoEmparejamientoRespuesta,
)
async def generar_codigo_emparejamiento(
    caso_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> CodigoEmparejamientoRespuesta:
    cfg = obtener_configuracion()
    try:
        resultado = await generar_codigo_para_caso(sesion, caso_id, cfg)
    except EmparejamientoError as exc:
        raise _http_desde_emparejamiento(exc) from exc

    return CodigoEmparejamientoRespuesta(
        caso_id=resultado.caso_id,
        codigo=resultado.codigo,
        expira_at=resultado.expira_at,
    )
