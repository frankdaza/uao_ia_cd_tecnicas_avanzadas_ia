"""Rutas administrativas del catalogo de procedimientos (UC-MVP-01)."""

from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi import status as estado_http
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencias import requerir_acceso_admin
from src.api.esquemas_procedimientos import (
    ListadoProcedimientosRespuesta,
    MetadataProcedimientoCuerpo,
    MetadataProcedimientoParche,
    ProcedimientoVista,
)
from src.api.servicios.ingesta_protocolo import ingesta_protocolo_background
from src.api.servicios.almacenamiento_protocolo import (
    ArchivoProtocoloInvalidoError,
    guardar_protocolo_en_disco,
    hash_sha256,
    http_422_desde_error_protocolo,
    leer_y_validar_archivo_protocolo,
    ruta_relativa_protocolo,
)
from src.configuracion import obtener_configuracion
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento

router = APIRouter(
    prefix="/admin",
    tags=["admin-procedimientos"],
    dependencies=[Depends(requerir_acceso_admin)],
)


def _a_vista(fila) -> ProcedimientoVista:
    return ProcedimientoVista.model_validate(fila)


def _parsear_metadata_crear(raw: str) -> MetadataProcedimientoCuerpo:
    try:
        datos = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"metadata JSON invalido: {exc}",
        ) from exc
    try:
        return MetadataProcedimientoCuerpo.model_validate(datos)
    except ValidationError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(),
        ) from exc


def _parsear_metadata_parche(raw: str | None) -> MetadataProcedimientoParche | None:
    if raw is None or not raw.strip():
        return None
    try:
        datos = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"metadata JSON invalido: {exc}",
        ) from exc
    try:
        return MetadataProcedimientoParche.model_validate(datos)
    except ValidationError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(),
        ) from exc


def _siguiente_version_vector(actual: int | None) -> int:
    if actual is None:
        return 1
    return actual + 1


def _encolar_ingesta(
    request: Request,
    background: BackgroundTasks,
    tipo_id: uuid.UUID,
) -> None:
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        return
    background.add_task(ingesta_protocolo_background, factory, tipo_id)


@router.post(
    "/procedimientos",
    response_model=ProcedimientoVista,
    status_code=estado_http.HTTP_201_CREATED,
)
async def crear_procedimiento(
    request: Request,
    background: BackgroundTasks,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    metadata: Annotated[str, Form(..., description="JSON con codigo y nombre")],
    archivo: Annotated[
        UploadFile, File(..., description="Protocolo medico en PDF (.pdf) o Markdown (.md)")
    ],
) -> ProcedimientoVista:
    meta = _parsear_metadata_crear(metadata)
    cfg = obtener_configuracion()
    repo = RepositorioTiposProcedimiento(sesion)

    if await repo.obtener_por_codigo(meta.codigo):
        raise HTTPException(
            status_code=estado_http.HTTP_409_CONFLICT,
            detail=f"Ya existe un procedimiento con codigo '{meta.codigo}'.",
        )

    try:
        contenido, _, formato = await leer_y_validar_archivo_protocolo(archivo, cfg)
    except ArchivoProtocoloInvalidoError as exc:
        raise http_422_desde_error_protocolo(exc) from exc

    digest = hash_sha256(contenido)
    fila = await repo.crear(
        codigo=meta.codigo,
        nombre=meta.nombre,
        indexacion_estado="pendiente",
        formato_protocolo=formato,
    )
    ruta_rel = ruta_relativa_protocolo(fila.id, formato)
    try:
        guardar_protocolo_en_disco(fila.id, contenido, formato)
    except OSError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar el protocolo en almacenamiento.",
        ) from exc

    await repo.actualizar(
        fila,
        ruta_pdf=ruta_rel,
        hash_pdf=digest,
        formato_protocolo=formato,
    )
    await sesion.commit()
    _encolar_ingesta(request, background, fila.id)
    return _a_vista(fila)


@router.get("/procedimientos", response_model=ListadoProcedimientosRespuesta)
async def listar_procedimientos(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListadoProcedimientosRespuesta:
    repo = RepositorioTiposProcedimiento(sesion)
    filas = await repo.listar(limite=limit, offset=offset)
    return ListadoProcedimientosRespuesta(
        items=[_a_vista(f) for f in filas],
        limit=limit,
        offset=offset,
    )


@router.get("/procedimientos/{tipo_id}", response_model=ProcedimientoVista)
async def obtener_procedimiento(
    tipo_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> ProcedimientoVista:
    repo = RepositorioTiposProcedimiento(sesion)
    fila = await repo.obtener_por_id(tipo_id)
    if fila is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado.",
        )
    return _a_vista(fila)


@router.patch("/procedimientos/{tipo_id}", response_model=ProcedimientoVista)
async def actualizar_procedimiento(
    request: Request,
    background: BackgroundTasks,
    tipo_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    metadata: Annotated[str | None, Form(description="JSON parcial: codigo, nombre")] = None,
    archivo: Annotated[
        UploadFile | None,
        File(description="Protocolo de reemplazo en PDF o Markdown (opcional)"),
    ] = None,
) -> ProcedimientoVista:
    meta = _parsear_metadata_parche(metadata)
    cfg = obtener_configuracion()
    repo = RepositorioTiposProcedimiento(sesion)
    fila = await repo.obtener_por_id(tipo_id)
    if fila is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado.",
        )

    if meta is not None and meta.codigo is not None and meta.codigo != fila.codigo:
        existente = await repo.obtener_por_codigo(meta.codigo)
        if existente is not None and existente.id != fila.id:
            raise HTTPException(
                status_code=estado_http.HTTP_409_CONFLICT,
                detail=f"Ya existe un procedimiento con codigo '{meta.codigo}'.",
            )

    kwargs: dict = {}
    if meta is not None:
        if meta.codigo is not None:
            kwargs["codigo"] = meta.codigo
        if meta.nombre is not None:
            kwargs["nombre"] = meta.nombre

    reemplazo_protocolo = archivo is not None and (archivo.filename or "").strip()
    if reemplazo_protocolo:
        try:
            contenido, _, formato = await leer_y_validar_archivo_protocolo(archivo, cfg)
        except ArchivoProtocoloInvalidoError as exc:
            raise http_422_desde_error_protocolo(exc) from exc
        digest = hash_sha256(contenido)
        ruta_anterior = fila.ruta_pdf
        try:
            guardar_protocolo_en_disco(
                fila.id,
                contenido,
                formato,
                ruta_anterior=ruta_anterior,
            )
        except OSError as exc:
            raise HTTPException(
                status_code=estado_http.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo guardar el protocolo en almacenamiento.",
            ) from exc
        kwargs["ruta_pdf"] = ruta_relativa_protocolo(fila.id, formato)
        kwargs["hash_pdf"] = digest
        kwargs["formato_protocolo"] = formato
        kwargs["indexacion_estado"] = "pendiente"
        kwargs["qdrant_collection_version"] = _siguiente_version_vector(
            fila.qdrant_collection_version
        )

    if not kwargs:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Debe enviar metadata y/o archivo de protocolo para actualizar.",
        )

    await repo.actualizar(fila, **kwargs)
    if reemplazo_protocolo:
        await sesion.commit()
        _encolar_ingesta(request, background, fila.id)
    else:
        await sesion.commit()
    return _a_vista(fila)


@router.post(
    "/procedimientos/{tipo_id}/reindexar",
    response_model=ProcedimientoVista,
    status_code=estado_http.HTTP_202_ACCEPTED,
)
async def reindexar_procedimiento(
    request: Request,
    background: BackgroundTasks,
    tipo_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> ProcedimientoVista:
    """Relanza ingesta Qdrant (util si fallo previa o tras cambio manual)."""
    repo = RepositorioTiposProcedimiento(sesion)
    fila = await repo.obtener_por_id(tipo_id)
    if fila is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado.",
        )
    if not fila.ruta_pdf:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El procedimiento no tiene archivo de protocolo asociado.",
        )
    await repo.actualizar(fila, indexacion_estado="pendiente")
    await sesion.commit()
    _encolar_ingesta(request, background, fila.id)
    return _a_vista(fila)
