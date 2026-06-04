"""Rutas staff de seguimiento: alertas y conversaciones (UC-MVP-05)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as estado_http
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.agente_taam import construir_agente_taam
from src.agentes.servicio import continuar_despues_hitl, requiere_revision_humana
from src.api.dependencias import (
    obtener_checkpointer_app,
    obtener_session_factory_app,
    obtener_staff_actual,
)
from src.api.esquemas_seguimiento import (
    AlertaTriageVista,
    CasoResumenSeguimientoRespuesta,
    ConversacionCasoRespuesta,
    ListadoAlertasRespuesta,
    MarcarAlertaRevisadaCuerpo,
    MensajeConversacionVista,
    ReanudarHitlCuerpo,
    ReanudarHitlRespuesta,
)
from src.api.privacidad_staff import enmascarar_chat_id_telegram
from src.api.servicios.historial_conversacion import listar_mensajes_hilo
from src.api.servicios.seguimiento_caso import alerta_a_vista, obtener_resumen_caso
from src.persistencia.modelos import UsuarioStaff
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

router = APIRouter(
    prefix="/staff",
    tags=["staff-seguimiento"],
    dependencies=[Depends(obtener_staff_actual)],
)


@router.get("/alertas", response_model=ListadoAlertasRespuesta)
async def listar_alertas_triage(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    staff: Annotated[UsuarioStaff, Depends(obtener_staff_actual)],
    revisado: Annotated[bool, Query()] = False,
    severidad: Annotated[
        str | None,
        Query(pattern="^(info|seguimiento|urgente)$"),
    ] = None,
    caso_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListadoAlertasRespuesta:
    """Bandeja de alertas de triage con filtros y paginacion."""
    repo_alertas = RepositorioAlertasTriage(sesion)
    filas = await repo_alertas.listar(
        revisado=revisado,
        severidad=severidad,
        caso_id=caso_id,
        limite=limit,
        offset=offset,
    )
    repo_casos = RepositorioCasosPostoperatorio(sesion)
    items: list[AlertaTriageVista] = []
    for alerta in filas:
        caso = await repo_casos.obtener_por_id(alerta.caso_id)
        if caso is None:
            continue
        items.append(alerta_a_vista(alerta, caso, rol_staff=staff.rol))
    return ListadoAlertasRespuesta(items=items, limit=limit, offset=offset)


@router.patch("/alertas/{alerta_id}", response_model=AlertaTriageVista)
async def marcar_alerta_revisada(
    alerta_id: uuid.UUID,
    cuerpo: MarcarAlertaRevisadaCuerpo,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    staff: Annotated[UsuarioStaff, Depends(obtener_staff_actual)],
) -> AlertaTriageVista:
    """Marca una alerta como revisada (idempotente)."""
    if not cuerpo.revisado:
        raise HTTPException(
            status_code=estado_http.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se admite revisado=true en MVP.",
        )

    repo_alertas = RepositorioAlertasTriage(sesion)
    alerta = await repo_alertas.obtener_por_id(alerta_id)
    if alerta is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada.",
        )

    await repo_alertas.marcar_revisado(
        alerta,
        staff_id=staff.id,
        revisado_at=datetime.now(UTC),
    )
    await sesion.commit()
    await sesion.refresh(alerta)

    repo_casos = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_casos.obtener_por_id(alerta.caso_id)
    if caso is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Caso asociado a la alerta no encontrado.",
        )
    return alerta_a_vista(alerta, caso, rol_staff=staff.rol)


@router.get(
    "/casos/{caso_id}/conversacion",
    response_model=ConversacionCasoRespuesta,
)
async def obtener_conversacion_caso(
    caso_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    staff: Annotated[UsuarioStaff, Depends(obtener_staff_actual)],
    checkpointer: Annotated[BaseCheckpointSaver, Depends(obtener_checkpointer_app)],
) -> ConversacionCasoRespuesta:
    """Historial paciente-bot desde el checkpointer (thread ``telegram:{chat_id}``)."""
    repo_casos = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_casos.obtener_por_id(caso_id)
    if caso is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Caso no encontrado.",
        )

    repo_vinculos = RepositorioVinculosTelegram(sesion)
    vinculo = await repo_vinculos.obtener_vinculado_por_caso(caso_id)
    if vinculo is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail=(
                "El caso no tiene vinculo Telegram activo; no hay conversacion que mostrar."
            ),
        )

    session_id = f"telegram:{vinculo.telegram_chat_id}"
    mensajes: list[MensajeConversacionVista] = await listar_mensajes_hilo(
        checkpointer,
        session_id,
    )
    return ConversacionCasoRespuesta(
        caso_id=caso_id,
        session_id=session_id,
        telegram_chat_id_enmascarado=enmascarar_chat_id_telegram(
            vinculo.telegram_chat_id,
            staff.rol,
        ),
        mensajes=mensajes,
    )


@router.post(
    "/casos/{caso_id}/reanudar-hitl",
    response_model=ReanudarHitlRespuesta,
)
async def reanudar_hitl_caso(
    caso_id: uuid.UUID,
    cuerpo: ReanudarHitlCuerpo,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(obtener_session_factory_app),
    ],
    checkpointer: Annotated[BaseCheckpointSaver, Depends(obtener_checkpointer_app)],
) -> ReanudarHitlRespuesta:
    """
    Reanuda el grafo tras interrupcion HITL en ``escalar_a_equipo`` (approve/reject).

    Si no hay interrupcion pendiente, responde ``reanudado=false`` sin error.
    """
    repo_casos = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_casos.obtener_por_id(caso_id)
    if caso is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Caso no encontrado.",
        )

    repo_vinculos = RepositorioVinculosTelegram(sesion)
    vinculo = await repo_vinculos.obtener_vinculado_por_caso(caso_id)
    if vinculo is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="El caso no tiene vinculo Telegram activo.",
        )

    session_id = f"telegram:{vinculo.telegram_chat_id}"
    agente = construir_agente_taam(checkpointer)
    snap = await agente.aget_state({"configurable": {"thread_id": session_id}})
    if snap is None or not snap.next:
        return ReanudarHitlRespuesta(
            caso_id=caso_id,
            session_id=session_id,
            decision=cuerpo.decision,
            requiere_revision_humana=False,
            reanudado=False,
        )

    estado = await continuar_despues_hitl(
        session_factory=session_factory,
        checkpointer=checkpointer,
        session_id=session_id,
        decision=cuerpo.decision,
    )
    return ReanudarHitlRespuesta(
        caso_id=caso_id,
        session_id=session_id,
        decision=cuerpo.decision,
        requiere_revision_humana=requiere_revision_humana(estado),
        reanudado=True,
    )


@router.get(
    "/casos/{caso_id}/resumen",
    response_model=CasoResumenSeguimientoRespuesta,
)
async def obtener_resumen_caso_staff(
    caso_id: uuid.UUID,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    staff: Annotated[UsuarioStaff, Depends(obtener_staff_actual)],
    checkpointer: Annotated[BaseCheckpointSaver, Depends(obtener_checkpointer_app)],
) -> CasoResumenSeguimientoRespuesta:
    """Ultimo triage, conteo de mensajes y proximo recordatorio pendiente."""
    resumen = await obtener_resumen_caso(
        sesion,
        checkpointer,
        caso_id=caso_id,
        staff=staff,
    )
    if resumen is None:
        raise HTTPException(
            status_code=estado_http.HTTP_404_NOT_FOUND,
            detail="Caso no encontrado.",
        )
    return resumen
