"""Envio programado y disparo manual de recordatorios Telegram (UC-MVP-04)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import Configuracion, obtener_configuracion
from src.integracion.recordatorios.programacion import (
    calcular_programado_at,
    renderizar_texto_plantilla,
)
from src.integracion.recordatorios.semilla_plantillas import (
    asegurar_plantillas_defecto,
    texto_cuidado_para_plantilla,
)
from src.integracion.telegram.cliente import ClienteTelegram
from src.persistencia.modelos import CasoPostoperatorio, RecordatorioEnviado
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.plantillas_recordatorio import (
    RepositorioPlantillasRecordatorio,
)
from src.persistencia.repositorios.recordatorios_enviados import (
    RepositorioRecordatoriosEnviados,
)
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

logger = logging.getLogger(__name__)


def _en_utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


@dataclass(frozen=True)
class ResultadoEnvioRecordatorio:
    recordatorio_id: uuid.UUID | None
    enviado: bool
    mensaje: str | None = None
    motivo_omitido: str | None = None


async def programar_recordatorios_para_caso(
    sesion: AsyncSession,
    caso: CasoPostoperatorio,
) -> list[RecordatorioEnviado]:
    """
    Crea filas ``recordatorios_enviados`` por cada plantilla del tipo de procedimiento.

    Invocar tras alta de caso (TASK-102). Asegura plantillas semilla si faltan.
    """
    await asegurar_plantillas_defecto(sesion, caso.tipo_procedimiento_id)
    repo_plantillas = RepositorioPlantillasRecordatorio(sesion)
    repo_recordatorios = RepositorioRecordatoriosEnviados(sesion)
    plantillas = await repo_plantillas.listar_por_tipo(caso.tipo_procedimiento_id)

    programados: list[RecordatorioEnviado] = []
    for plantilla in plantillas:
        programado_at = calcular_programado_at(
            caso.fecha_cirugia,
            plantilla.offset_horas_desde_cirugia,
        )
        fila = await repo_recordatorios.crear(
            caso_id=caso.id,
            plantilla_id=plantilla.id,
            programado_at=programado_at,
        )
        programados.append(fila)
    return programados


async def procesar_recordatorios_pendientes(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    cfg: Configuracion | None = None,
    cliente_telegram: ClienteTelegram | None = None,
) -> int:
    """
    Busca recordatorios vencidos y pendientes; devuelve cantidad enviada con exito.

    Sin email ni otros canales (solo Telegram Bot API, TASK-106).
    """
    conf = cfg or obtener_configuracion()
    cliente = cliente_telegram or ClienteTelegram(conf)
    ahora = datetime.now(UTC)
    enviados = 0

    async with session_factory() as sesion:
        repo = RepositorioRecordatoriosEnviados(sesion)
        pendientes = await repo.listar_pendientes_vencidos(ahora=ahora)
        for recordatorio in pendientes:
            resultado = await _enviar_recordatorio(
                sesion,
                recordatorio,
                cliente=cliente,
                ignorar_programado=False,
            )
            if resultado.enviado:
                enviados += 1
        await sesion.commit()

    return enviados


async def disparar_recordatorio_prueba(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
    *,
    cfg: Configuracion | None = None,
    cliente_telegram: ClienteTelegram | None = None,
) -> ResultadoEnvioRecordatorio:
    """
    Envio manual del siguiente recordatorio pendiente del caso (demo UC-MVP-04).

    No exige que ``programado_at`` haya pasado.
    """
    conf = cfg or obtener_configuracion()
    cliente = cliente_telegram or ClienteTelegram(conf)
    repo_casos = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_casos.obtener_por_id(caso_id)
    if caso is None:
        return ResultadoEnvioRecordatorio(
            recordatorio_id=None,
            enviado=False,
            motivo_omitido="caso_inexistente",
            mensaje="El caso no existe.",
        )

    repo_rec = RepositorioRecordatoriosEnviados(sesion)
    recordatorio = await repo_rec.obtener_siguiente_pendiente_caso(caso_id)
    if recordatorio is None:
        await asegurar_plantillas_defecto(sesion, caso.tipo_procedimiento_id)
        await programar_recordatorios_para_caso(sesion, caso)
        recordatorio = await repo_rec.obtener_siguiente_pendiente_caso(caso_id)
    if recordatorio is None:
        return ResultadoEnvioRecordatorio(
            recordatorio_id=None,
            enviado=False,
            motivo_omitido="sin_recordatorios_pendientes",
            mensaje="No hay recordatorios pendientes para este caso.",
        )

    return await _enviar_recordatorio(
        sesion,
        recordatorio,
        cliente=cliente,
        ignorar_programado=True,
    )


async def _enviar_recordatorio(
    sesion: AsyncSession,
    recordatorio: RecordatorioEnviado,
    *,
    cliente: ClienteTelegram,
    ignorar_programado: bool,
) -> ResultadoEnvioRecordatorio:
    if recordatorio.estado != "pendiente" or recordatorio.enviado_at is not None:
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="ya_procesado",
            mensaje="El recordatorio ya fue enviado o cancelado.",
        )

    ahora = datetime.now(UTC)
    programado = _en_utc(recordatorio.programado_at)
    if not ignorar_programado and programado > ahora:
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="aun_no_vencido",
            mensaje="El recordatorio aun no esta programado para envio.",
        )

    repo_casos = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_casos.obtener_por_id(recordatorio.caso_id)
    if caso is None:
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="caso_inexistente",
            mensaje="El caso asociado al recordatorio no existe.",
        )

    repo_plantillas = RepositorioPlantillasRecordatorio(sesion)
    plantilla = await repo_plantillas.obtener_por_id(recordatorio.plantilla_id)
    if plantilla is None:
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="plantilla_inexistente",
            mensaje="La plantilla del recordatorio no existe.",
        )

    repo_vinculos = RepositorioVinculosTelegram(sesion)
    vinculo = await repo_vinculos.obtener_vinculado_por_caso(caso.id)
    if vinculo is None:
        logger.info(
            "recordatorio_omitido_sin_telegram caso_id=%s recordatorio_id=%s",
            caso.id,
            recordatorio.id,
        )
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="sin_vinculo_telegram",
            mensaje="El caso no tiene vinculo Telegram activo.",
        )

    repo_tipos = RepositorioTiposProcedimiento(sesion)
    tipo = await repo_tipos.obtener_por_id(caso.tipo_procedimiento_id)
    nombre_tipo = tipo.nombre if tipo is not None else "su procedimiento"

    texto = renderizar_texto_plantilla(
        plantilla.texto_plantilla,
        nombre_paciente=caso.paciente_nombre,
        tipo_procedimiento=nombre_tipo,
        texto_cuidado=texto_cuidado_para_plantilla(plantilla.tipo),
    )

    try:
        await cliente.enviar_mensaje(vinculo.telegram_chat_id, texto)
    except Exception:
        logger.exception(
            "recordatorio_envio_fallo recordatorio_id=%s chat_id=%s",
            recordatorio.id,
            vinculo.telegram_chat_id,
        )
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        await repo_rec.marcar_error(recordatorio)
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="error_telegram",
            mensaje="No se pudo enviar el mensaje por Telegram.",
        )

    repo_rec = RepositorioRecordatoriosEnviados(sesion)
    await repo_rec.marcar_enviado(recordatorio, enviado_at=ahora)
    logger.info(
        "recordatorio_enviado recordatorio_id=%s caso_id=%s chat_id=%s",
        recordatorio.id,
        caso.id,
        vinculo.telegram_chat_id,
    )
    return ResultadoEnvioRecordatorio(
        recordatorio_id=recordatorio.id,
        enviado=True,
        mensaje=texto,
    )
