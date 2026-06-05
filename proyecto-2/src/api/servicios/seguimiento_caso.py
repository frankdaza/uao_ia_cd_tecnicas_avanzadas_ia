"""Resumen operativo de un caso para el panel staff."""

from __future__ import annotations

import uuid

from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.esquemas_seguimiento import AlertaTriageVista, CasoResumenSeguimientoRespuesta
from src.api.privacidad_staff import enmascarar_chat_id_telegram, enmascarar_valor_sensible
from src.api.servicios.historial_conversacion import (
    contar_mensajes_hilo,
    listar_mensajes_hilo,
)
from src.persistencia.modelos import AlertaTriage, CasoPostoperatorio, UsuarioStaff
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.recordatorios_enviados import (
    RepositorioRecordatoriosEnviados,
)
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram


async def obtener_resumen_caso(
    sesion: AsyncSession,
    checkpointer: BaseCheckpointSaver,
    *,
    caso_id: uuid.UUID,
    staff: UsuarioStaff,
) -> CasoResumenSeguimientoRespuesta | None:
    repo_casos = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_casos.obtener_por_id(caso_id)
    if caso is None:
        return None

    return await _resumen_desde_caso(sesion, checkpointer, caso=caso, staff=staff)


async def _resumen_desde_caso(
    sesion: AsyncSession,
    checkpointer: BaseCheckpointSaver,
    *,
    caso: CasoPostoperatorio,
    staff: UsuarioStaff,
) -> CasoResumenSeguimientoRespuesta:
    repo_vinculos = RepositorioVinculosTelegram(sesion)
    vinculo_activo = await repo_vinculos.obtener_vinculado_por_caso(caso.id)
    hilo = vinculo_activo or await repo_vinculos.obtener_ultimo_hilo_telegram_por_caso(caso.id)

    conteo = 0
    chat_enmascarado: str | None = None
    if hilo is not None:
        session_id = f"telegram:{hilo.telegram_chat_id}"
        mensajes = await listar_mensajes_hilo(checkpointer, session_id)
        conteo = contar_mensajes_hilo(mensajes)
        chat_enmascarado = enmascarar_chat_id_telegram(
            hilo.telegram_chat_id,
            staff.rol,
        )

    repo_alertas = RepositorioAlertasTriage(sesion)
    ultima = await repo_alertas.obtener_ultima_por_caso(caso.id)

    repo_recordatorios = RepositorioRecordatoriosEnviados(sesion)
    proximo = await repo_recordatorios.obtener_siguiente_pendiente_caso(caso.id)

    return CasoResumenSeguimientoRespuesta(
        caso_id=caso.id,
        ultima_severidad=ultima.severidad if ultima else None,
        ultima_alerta_resumen=ultima.resumen if ultima else None,
        ultima_alerta_created_at=ultima.created_at if ultima else None,
        conteo_mensajes=conteo,
        proximo_recordatorio_at=proximo.programado_at if proximo else None,
        proximo_recordatorio_estado=proximo.estado if proximo else None,
        telegram_chat_id_enmascarado=chat_enmascarado,
        vinculado_telegram=vinculo_activo is not None,
    )


def alerta_a_vista(
    alerta: AlertaTriage,
    caso: CasoPostoperatorio,
    *,
    rol_staff: str,
) -> AlertaTriageVista:
    return AlertaTriageVista(
        id=alerta.id,
        caso_id=alerta.caso_id,
        paciente_doc_id=enmascarar_valor_sensible(caso.paciente_doc_id, rol_staff),
        paciente_nombre=caso.paciente_nombre,
        severidad=alerta.severidad,
        resumen=alerta.resumen,
        mensaje_paciente_ref=alerta.mensaje_paciente_ref,
        revisado=alerta.revisado,
        revisado_at=alerta.revisado_at,
        revisado_staff_id=alerta.revisado_staff_id,
        created_at=alerta.created_at,
    )
