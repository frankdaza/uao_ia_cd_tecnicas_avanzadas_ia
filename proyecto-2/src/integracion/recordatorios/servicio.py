"""Envio programado y disparo manual de recordatorios Telegram (UC-MVP-04)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import Configuracion, obtener_configuracion
from src.integracion.recordatorios.programacion import (
    calcular_programado_at_por_intervalo,
    renderizar_texto_plantilla,
)
from src.integracion.recordatorios.semilla_plantillas import (
    asegurar_plantillas_defecto,
    texto_cuidado_para_plantilla,
)
from src.integracion.telegram.cliente import ClienteTelegram
from src.integracion.telegram.errores import TelegramEnvioError, es_error_envio_esperado
from src.persistencia.demo_ids import es_chat_id_demo_ficticio
from src.persistencia.modelos import CasoPostoperatorio, RecordatorioEnviado
from src.persistencia.repositorios.config_operativa_taam import RepositorioConfigOperativaTaam
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


async def _interval_seg_efectivo(sesion: AsyncSession) -> int:
    repo_cfg = RepositorioConfigOperativaTaam(sesion)
    fila = await repo_cfg.obtener()
    if fila is not None:
        return fila.recordatorios_job_interval_seg
    return obtener_configuracion().recordatorios_job_interval_seg


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


@dataclass(frozen=True)
class ResultadoCicloRecordatorios:
    """Metricas de un ciclo del job periodico (observabilidad)."""

    pendientes_vencidos: int
    enviados: int


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
    plantillas = sorted(
        await repo_plantillas.listar_por_tipo(caso.tipo_procedimiento_id),
        key=lambda p: p.offset_horas_desde_cirugia,
    )
    interval_seg = await _interval_seg_efectivo(sesion)
    ancla = datetime.now(UTC)

    programados: list[RecordatorioEnviado] = []
    for indice, plantilla in enumerate(plantillas):
        programado_at = calcular_programado_at_por_intervalo(
            ancla,
            indice,
            interval_seg,
        )
        fila = await repo_recordatorios.crear(
            caso_id=caso.id,
            plantilla_id=plantilla.id,
            programado_at=programado_at,
        )
        programados.append(fila)
    return programados


async def reprogramar_recordatorios_pendientes(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    interval_seg: int,
) -> int:
    """
    Reasigna ``programado_at`` de todos los pendientes según el intervalo del panel admin.

    Reinicia la cadena desde ``now`` por caso (medicación → terapia → control).
    """
    ancla = datetime.now(UTC)
    reprogramados = 0

    async with session_factory() as sesion:
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        repo_pl = RepositorioPlantillasRecordatorio(sesion)
        pendientes = await repo_rec.listar_pendientes_sin_enviar()

        por_caso: dict[uuid.UUID, list[RecordatorioEnviado]] = {}
        for fila in pendientes:
            por_caso.setdefault(fila.caso_id, []).append(fila)

        for filas_caso in por_caso.values():
            ordenadas: list[tuple[int, RecordatorioEnviado]] = []
            for fila in filas_caso:
                plantilla = await repo_pl.obtener_por_id(fila.plantilla_id)
                offset = plantilla.offset_horas_desde_cirugia if plantilla else 0
                ordenadas.append((offset, fila))
            ordenadas.sort(key=lambda t: t[0])

            for indice, (_, fila) in enumerate(ordenadas):
                nuevo = calcular_programado_at_por_intervalo(ancla, indice, interval_seg)
                await repo_rec.actualizar_programado_at(fila, programado_at=nuevo)
                reprogramados += 1

        await sesion.commit()

    if reprogramados:
        logger.info(
            "recordatorios_reprogramados cantidad=%s interval_seg=%s",
            reprogramados,
            interval_seg,
        )
    return reprogramados


async def procesar_recordatorios_pendientes(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    cfg: Configuracion | None = None,
    cliente_telegram: ClienteTelegram | None = None,
) -> ResultadoCicloRecordatorios:
    """
    Busca recordatorios vencidos y pendientes; devuelve metricas del ciclo.

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

    return ResultadoCicloRecordatorios(
        pendientes_vencidos=len(pendientes),
        enviados=enviados,
    )


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

    if es_chat_id_demo_ficticio(vinculo.telegram_chat_id):
        logger.info(
            "recordatorio_omitido_chat_demo caso_id=%s recordatorio_id=%s chat_id=%s",
            caso.id,
            recordatorio.id,
            vinculo.telegram_chat_id,
        )
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="chat_demo_ficticio",
            mensaje=(
                "El chat_id de la semilla demo no es valido en Telegram; "
                "empareje un chat real o use disparar-recordatorio-prueba tras /start."
            ),
        )

    texto = renderizar_texto_plantilla(
        plantilla.texto_plantilla,
        nombre_paciente=caso.paciente_nombre,
        tipo_procedimiento=nombre_tipo,
        texto_cuidado=texto_cuidado_para_plantilla(plantilla.tipo),
    )

    try:
        await cliente.enviar_mensaje(vinculo.telegram_chat_id, texto)
    except TelegramEnvioError as exc:
        if es_error_envio_esperado(exc.cuerpo):
            logger.warning(
                "recordatorio_envio_fallo recordatorio_id=%s chat_id=%s status=%s",
                recordatorio.id,
                vinculo.telegram_chat_id,
                exc.status_code,
            )
        else:
            logger.error(
                "recordatorio_envio_fallo recordatorio_id=%s chat_id=%s status=%s body=%s",
                recordatorio.id,
                vinculo.telegram_chat_id,
                exc.status_code,
                exc.cuerpo[:200],
            )
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        await repo_rec.marcar_error(recordatorio)
        return ResultadoEnvioRecordatorio(
            recordatorio_id=recordatorio.id,
            enviado=False,
            motivo_omitido="error_telegram",
            mensaje="No se pudo enviar el mensaje por Telegram.",
        )
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
