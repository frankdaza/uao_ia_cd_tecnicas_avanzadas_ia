"""
Rutas administrativas M2 (clave estatica ``ADMIN_API_KEY`` / cabecera ``X-Admin-Key``).
"""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi import status as estado_http
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.configuracion import obtener_configuracion
from src.api.dependencias import obtener_sesion_db
from src.api.esquemas_admin import (
    EstadoConfigAdminM2Respuesta,
    ListadoUsuariosAdminRespuesta,
    MetricasAdminResumen,
    ParcheConfigAdminM2Cuerpo,
    UsuarioAdminVista,
)
from src.api.servicios.agente_m2_config import ConflictoVersionConfigAdminError, ServicioAgenteM2Config
from src.persistencia.repositorios.usuarios import RepositorioUsuarios

router = APIRouter(prefix="/admin", tags=["admin"])


def _enmascarar_documento_identidad(valor: str) -> str:
    v = valor.strip()
    if len(v) <= 4:
        return "****"
    return f"{v[:2]}***{v[-2:]}"


async def requerir_clave_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> None:
    """Rechaza peticiones sin clave admin valida (comparacion en tiempo constante si longitudes coinciden)."""
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


async def _construir_estado_config_respuesta(
    sesion: AsyncSession,
) -> EstadoConfigAdminM2Respuesta:
    svc = ServicioAgenteM2Config(sesion)
    fila = await svc.obtener_fila()
    meta = svc.fusionar_meta_prompt(fila)
    return EstadoConfigAdminM2Respuesta(
        version=int(fila.version) if fila is not None else 0,
        updated_at=fila.updated_at if fila is not None else None,
        modelo_llm_router=svc.modelo_router_efectivo(fila),
        modelo_llm_compositor=svc.modelo_compositor_efectivo(fila),
        temperatura_router=svc.temperatura_router_efectiva(fila),
        temperatura_compositor=svc.temperatura_compositor_efectiva(fila),
        top_p_router=svc.top_p_router_efectivo(fila),
        top_p_compositor=svc.top_p_compositor_efectivo(fila),
        model_kwargs_router=svc.kwargs_router(fila),
        model_kwargs_compositor=svc.kwargs_compositor(fila),
        meta_prompt=meta.model_dump(),
        prompt_institucional=svc.prompt_institucional_efectivo(fila),
        rag_top_k=svc.rag_top_k_efectivo(fila),
        rag_score_minimo=svc.rag_score_minimo_efectivo(fila),
    )


@router.get(
    "/config",
    response_model=EstadoConfigAdminM2Respuesta,
    dependencies=[Depends(requerir_clave_admin)],
    summary="Obtener configuracion efectiva del agente M2",
    description=(
        "Devuelve valores ya fusionados (PostgreSQL > archivo JSON > .env > constantes de codigo). "
        "Parametros como ``top_k`` de proveedores distintos a la API de chat OpenAI deben ir en "
        "``model_kwargs_*``; muchos modelos de chat OpenAI ignoran ``top_k`` en favor de ``top_p``."
    ),
)
async def obtener_config_admin_m2(
    sesion: AsyncSession = Depends(obtener_sesion_db),
) -> EstadoConfigAdminM2Respuesta:
    return await _construir_estado_config_respuesta(sesion)


@router.patch(
    "/config",
    response_model=EstadoConfigAdminM2Respuesta,
    dependencies=[Depends(requerir_clave_admin)],
    summary="Actualizar parametros y prompts persistidos (hot-reload)",
    description=(
        "Valida ``temperature`` en [0, 2] y ``top_p`` en [0, 1]. Los modelos, si se envian, no pueden ser "
        "cadenas vacias. La respuesta incluye ``version`` y ``updated_at`` tras persistir. "
        "El siguiente ``POST /api/agente/stream`` usa el nuevo snapshot; no se alteran streams SSE ya abiertos. "
        "Con ``MOCK_LLM=1`` los modelos OpenAI no se instancian, pero meta-prompt e institucional desde base de "
        "datos siguen aplicando al grafo."
    ),
)
async def parchear_config_admin_m2(
    cuerpo: ParcheConfigAdminM2Cuerpo,
    sesion: AsyncSession = Depends(obtener_sesion_db),
) -> EstadoConfigAdminM2Respuesta:
    svc = ServicioAgenteM2Config(sesion)
    datos = cuerpo.model_dump(exclude_unset=True)
    version = int(datos.pop("version"))
    kwargs_aplicar = {k: v for k, v in datos.items() if v is not None}
    try:
        await svc.aplicar_parche(version_esperada=version, **kwargs_aplicar)
    except ConflictoVersionConfigAdminError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_409_CONFLICT,
            detail="La configuracion fue modificada por otro proceso; recargue y reintente.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return await _construir_estado_config_respuesta(sesion)


@router.get(
    "/usuarios",
    response_model=ListadoUsuariosAdminRespuesta,
    dependencies=[Depends(requerir_clave_admin)],
    summary="Listar usuarios registrados (paginado)",
)
async def listar_usuarios_admin_m2(
    sesion: AsyncSession = Depends(obtener_sesion_db),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ListadoUsuariosAdminRespuesta:
    repo = RepositorioUsuarios(sesion)
    total = await repo.contar_total()
    filas = await repo.listar_paginado(limite=limit, offset=offset)
    items = [
        UsuarioAdminVista(
            id=u.id,
            nombre=u.nombre,
            documento_identidad_enmascarado=_enmascarar_documento_identidad(u.documento_identidad),
            created_at=u.created_at,
            updated_at=u.updated_at,
            last_login_at=u.last_login_at,
        )
        for u in filas
    ]
    return ListadoUsuariosAdminRespuesta(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/metricas/resumen",
    response_model=MetricasAdminResumen,
    dependencies=[Depends(requerir_clave_admin)],
    summary="Agregados ligeros para dashboard administrativo",
    description=(
        "Dos consultas ``COUNT`` sobre ``usuarios`` (total y activos con ``last_login_at`` en los ultimos 7 dias, "
        "comparacion en UTC en el servidor de aplicacion). Coste acotado a la cardinalidad de esa tabla; "
        "``sesiones_estimadas`` queda en 0 hasta existir modelo OLTP de sesiones."
    ),
)
async def metricas_resumen_admin_m2(
    sesion: AsyncSession = Depends(obtener_sesion_db),
) -> MetricasAdminResumen:
    repo = RepositorioUsuarios(sesion)
    total = await repo.contar_total()
    activos = await repo.contar_activos_ultimos_dias(7)
    return MetricasAdminResumen(
        usuarios_total=total,
        usuarios_activos_ultimos_7_dias=activos,
        sesiones_estimadas=0,
    )


__all__ = ["router", "requerir_clave_admin"]
