"""Rutas administrativas del catalogo de medicos/cirujanos."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as estado_http
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencias import requerir_acceso_admin
from src.api.esquemas_medicos import (
    ListadoMedicosRespuesta,
    MedicoCuerpo,
    MedicoParche,
    MedicoVista,
)
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.modelos import Medico
from src.persistencia.repositorios.medicos import RepositorioMedicos

router = APIRouter(
    prefix="/admin",
    tags=["admin-medicos"],
    dependencies=[Depends(requerir_acceso_admin)],
)


def _a_vista(fila: Medico) -> MedicoVista:
    return MedicoVista.model_validate(fila)


@router.post(
    "/medicos",
    response_model=MedicoVista,
    status_code=estado_http.HTTP_201_CREATED,
)
async def crear_medico(
    cuerpo: MedicoCuerpo,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> MedicoVista:
    repo = RepositorioMedicos(sesion)
    if await repo.obtener_por_codigo(cuerpo.codigo_registro):
        raise HTTPException(
            status_code=estado_http.HTTP_409_CONFLICT,
            detail=f"Ya existe un medico con codigo_registro '{cuerpo.codigo_registro}'.",
        )
    fila = await repo.crear(**cuerpo.model_dump())
    await sesion.commit()
    return _a_vista(fila)


@router.get("/medicos", response_model=ListadoMedicosRespuesta)
async def listar_medicos(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    activo: Annotated[bool | None, Query()] = None,
) -> ListadoMedicosRespuesta:
    repo = RepositorioMedicos(sesion)
    filas = await repo.listar(limite=limit, offset=offset, activo=activo)
    total = await repo.contar(activo=activo)
    return ListadoMedicosRespuesta(
        items=[_a_vista(f) for f in filas],
        total=total,
    )


@router.get("/medicos/{medico_id}", response_model=MedicoVista)
async def obtener_medico(
    medico_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> MedicoVista:
    repo = RepositorioMedicos(sesion)
    fila = await repo.obtener_por_id(medico_id)
    if fila is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Medico no encontrado.",
        )
    return _a_vista(fila)


@router.patch("/medicos/{medico_id}", response_model=MedicoVista)
async def actualizar_medico(
    medico_id: uuid.UUID,
    cuerpo: MedicoParche,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> MedicoVista:
    repo = RepositorioMedicos(sesion)
    fila = await repo.obtener_por_id(medico_id)
    if fila is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Medico no encontrado.",
        )

    datos = cuerpo.model_dump(exclude_unset=True)
    if not datos:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Debe enviar al menos un campo para actualizar.",
        )

    nuevo_codigo = datos.get("codigo_registro")
    if nuevo_codigo is not None and nuevo_codigo != fila.codigo_registro:
        existente = await repo.obtener_por_codigo(nuevo_codigo)
        if existente is not None and existente.id != fila.id:
            raise HTTPException(
                status_code=estado_http.HTTP_409_CONFLICT,
                detail=f"Ya existe un medico con codigo_registro '{nuevo_codigo}'.",
            )

    await repo.actualizar(fila, **datos)
    await sesion.commit()
    return _a_vista(fila)


@router.delete(
    "/medicos/{medico_id}",
    status_code=estado_http.HTTP_204_NO_CONTENT,
)
async def desactivar_medico(
    medico_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> None:
    repo = RepositorioMedicos(sesion)
    fila = await repo.obtener_por_id(medico_id)
    if fila is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Medico no encontrado.",
        )
    if await repo.existe_caso_activo_con_cirujano_id(fila.codigo_registro):
        raise HTTPException(
            status_code=estado_http.HTTP_409_CONFLICT,
            detail=(
                "No se puede desactivar el medico: existe un caso postoperatorio "
                "activo asociado a su codigo de registro."
            ),
        )
    await repo.actualizar(fila, activo=False)
    await sesion.commit()
