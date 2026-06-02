"""Semilla idempotente de datos demo TAAM (TASK-114)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.agente_taam import construir_agente_taam
from src.agentes.checkpointer import gestionar_checkpointer_postgres_async
from src.api.servicios.almacenamiento_protocolo import (
    guardar_protocolo_en_disco,
    hash_sha256,
    ruta_relativa_protocolo,
)
from src.configuracion import Configuracion
from src.integracion.recordatorios.servicio import programar_recordatorios_para_caso
from src.integracion.recordatorios.semilla_plantillas import asegurar_plantillas_defecto
from src.persistencia.modelos import AlertaTriage, CasoPostoperatorio
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram
from src.persistencia.semilla_staff_demo import sembrar_usuarios_staff_demo
from src.rutas_workspace import resolver_ruta_workspace

logger = logging.getLogger(__name__)

CODIGO_PROCEDIMIENTO_DEMO = "COLE-LAP-001"
NOMBRE_PROCEDIMIENTO_DEMO = "Colecistectomia laparoscopica (demo)"
RUTA_PDF_DEMO_REL = "data/taam/demo/colecistectomia-protocolo-sintetico.pdf"
CIRUJANO_ID_DEMO = "DOC-DEMO-001"
CIRUJANO_NOMBRE_DEMO = "Dr. Demo TAAM"

CHAT_TELEGRAM_CASO_A = 111111111
CHAT_TELEGRAM_CASO_B = 222222222
CODIGO_EMPAREJAMIENTO_CASO_B = "DEMO2X"

PACIENTE_DOC_A = "PAC-DEMO-001"
PACIENTE_NOMBRE_A = "Ana Ficticia Lopez"
PACIENTE_DOC_B = "PAC-DEMO-002"
PACIENTE_NOMBRE_B = "Bruno Ficticio Ruiz"


@dataclass(frozen=True)
class ResultadoSemillaDemo:
    """Resumen de la corrida de semilla demo."""

    emails_staff: list[str]
    tipo_procedimiento_id: uuid.UUID
    caso_a_id: uuid.UUID
    caso_b_id: uuid.UUID
    mensajes: list[str]


def _ruta_pdf_demo_fuente() -> Path:
    ruta = resolver_ruta_workspace(RUTA_PDF_DEMO_REL)
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No se encontro el PDF demo en {ruta}. "
            "Verifique data/taam/demo/colecistectomia-protocolo-sintetico.pdf en el workspace."
        )
    return ruta


async def _asegurar_tipo_procedimiento_demo(
    sesion: AsyncSession,
) -> tuple[uuid.UUID, str]:
    repo = RepositorioTiposProcedimiento(sesion)
    fila = await repo.obtener_por_codigo(CODIGO_PROCEDIMIENTO_DEMO)
    contenido = _ruta_pdf_demo_fuente().read_bytes()
    digest = hash_sha256(contenido)

    if fila is None:
        fila = await repo.crear(
            codigo=CODIGO_PROCEDIMIENTO_DEMO,
            nombre=NOMBRE_PROCEDIMIENTO_DEMO,
            indexacion_estado="pendiente",
            formato_protocolo="pdf",
        )
        await sesion.flush()
        mensaje = f"Tipo procedimiento creado: {CODIGO_PROCEDIMIENTO_DEMO}"
    else:
        mensaje = f"Tipo procedimiento actualizado: {CODIGO_PROCEDIMIENTO_DEMO}"

    guardar_protocolo_en_disco(fila.id, contenido, "pdf")
    await repo.actualizar(
        fila,
        nombre=NOMBRE_PROCEDIMIENTO_DEMO,
        ruta_pdf=ruta_relativa_protocolo(fila.id, "pdf"),
        hash_pdf=digest,
        formato_protocolo="pdf",
        indexacion_estado="ok",
        qdrant_collection_version=1,
    )
    await asegurar_plantillas_defecto(sesion, fila.id)
    return fila.id, mensaje


async def _asegurar_caso_demo(
    sesion: AsyncSession,
    *,
    paciente_doc_id: str,
    paciente_nombre: str,
    tipo_procedimiento_id: uuid.UUID,
    dias_desde_cirugia: int,
    notas: str | None = None,
) -> CasoPostoperatorio:
    repo = RepositorioCasosPostoperatorio(sesion)
    existente = await repo.obtener_activo_por_doc_id(paciente_doc_id)
    fecha_cirugia = date.today() - timedelta(days=dias_desde_cirugia)
    if existente is not None:
        existente.paciente_nombre = paciente_nombre
        existente.fecha_cirugia = fecha_cirugia
        existente.notas_especificas = notas
        existente.tipo_procedimiento_id = tipo_procedimiento_id
        await sesion.flush()
        caso = existente
    else:
        caso = await repo.crear(
            paciente_doc_id=paciente_doc_id,
            paciente_nombre=paciente_nombre,
            tipo_procedimiento_id=tipo_procedimiento_id,
            cirujano_id=CIRUJANO_ID_DEMO,
            cirujano_nombre=CIRUJANO_NOMBRE_DEMO,
            fecha_cirugia=fecha_cirugia,
            notas_especificas=notas,
        )

    await programar_recordatorios_para_caso(sesion, caso)
    return caso


async def _asegurar_vinculo_caso_a(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
) -> None:
    repo = RepositorioVinculosTelegram(sesion)
    vinculado = await repo.obtener_vinculado_por_caso(caso_id)
    ahora = datetime.now(UTC)
    if vinculado is None:
        await repo.crear(
            caso_id=caso_id,
            telegram_chat_id=CHAT_TELEGRAM_CASO_A,
            vinculado_at=ahora,
        )
        return
    if vinculado.telegram_chat_id != CHAT_TELEGRAM_CASO_A:
        await repo.actualizar(
            vinculado,
            telegram_chat_id=CHAT_TELEGRAM_CASO_A,
            vinculado_at=ahora,
            limpiar_codigo=True,
        )


async def _asegurar_codigo_pendiente_caso_b(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
    cfg: Configuracion,
) -> None:
    repo = RepositorioVinculosTelegram(sesion)
    vinculado = await repo.obtener_vinculado_por_caso(caso_id)
    if vinculado is not None and vinculado.vinculado_at is not None:
        return

    pendiente = await repo.obtener_pendiente_por_caso(caso_id)
    expira = datetime.now(UTC) + timedelta(hours=cfg.taam_codigo_emparejamiento_ttl_horas)
    if pendiente is None:
        await repo.crear(
            caso_id=caso_id,
            telegram_chat_id=CHAT_TELEGRAM_CASO_B,
            codigo_emparejamiento=CODIGO_EMPAREJAMIENTO_CASO_B,
            codigo_expira_at=expira,
        )
        return
    await repo.actualizar(
        pendiente,
        telegram_chat_id=CHAT_TELEGRAM_CASO_B,
        codigo_emparejamiento=CODIGO_EMPAREJAMIENTO_CASO_B,
        codigo_expira_at=expira,
    )


async def _asegurar_alerta_urgente_caso_a(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
) -> None:
    stmt = (
        select(AlertaTriage)
        .where(
            AlertaTriage.caso_id == caso_id,
            AlertaTriage.severidad == "urgente",
            AlertaTriage.revisado.is_(False),
        )
        .limit(1)
    )
    res = await sesion.execute(stmt)
    if res.scalars().first() is not None:
        return

    repo = RepositorioAlertasTriage(sesion)
    await repo.crear(
        caso_id=caso_id,
        severidad="urgente",
        resumen="Sangrado abundante en la herida (demo semilla)",
        mensaje_paciente_ref="Tengo sangrado abundante en la herida",
        tool_trace_json={"origen": "semilla_demo_taam", "demo": True},
    )


async def _sembrar_conversacion_caso_a(cfg: Configuracion) -> None:
    session_id = f"telegram:{CHAT_TELEGRAM_CASO_A}"
    async with gestionar_checkpointer_postgres_async(cfg.url_base_datos_sync()) as checkpointer:
        agente = construir_agente_taam(checkpointer)
        await agente.aupdate_state(
            {"configurable": {"thread_id": session_id}},
            {
                "messages": [
                    HumanMessage(content="¿Cuándo puedo retomar caminatas leves?"),
                    AIMessage(
                        content=(
                            "Segun su protocolo, puede iniciar caminatas cortas dentro de casa "
                            "desde el primer o segundo dia si lo tolera. Ante empeoramiento, "
                            "contacte a su equipo."
                        )
                    ),
                    HumanMessage(content="Tengo sangrado abundante en la herida"),
                    AIMessage(
                        content=(
                            "Eso puede ser un signo de alarma. Acuda a urgencias o contacte "
                            "de inmediato a su equipo tratante. Este mensaje fue escalado al "
                            "personal clinico."
                        )
                    ),
                ]
            },
        )


async def sembrar_demo_taam(
    session_factory: async_sessionmaker[AsyncSession],
    cfg: Configuracion,
    *,
    sembrar_conversacion: bool = True,
) -> ResultadoSemillaDemo:
    """
    Semilla completa para sustentacion: staff, procedimiento, casos, alerta e hilo.

    Idempotente: puede ejecutarse varias veces sin duplicar entidades clave.
    """
    mensajes: list[str] = []

    async with session_factory() as sesion:
        emails = await sembrar_usuarios_staff_demo(sesion, cfg)
        mensajes.append(f"Staff demo: {', '.join(emails)}")

        tipo_id, msg_tipo = await _asegurar_tipo_procedimiento_demo(sesion)
        mensajes.append(msg_tipo)

        caso_a = await _asegurar_caso_demo(
            sesion,
            paciente_doc_id=PACIENTE_DOC_A,
            paciente_nombre=PACIENTE_NOMBRE_A,
            tipo_procedimiento_id=tipo_id,
            dias_desde_cirugia=2,
            notas="Caso demo A: emparejado y alerta urgente para UC-MVP-05.",
        )
        caso_b = await _asegurar_caso_demo(
            sesion,
            paciente_doc_id=PACIENTE_DOC_B,
            paciente_nombre=PACIENTE_NOMBRE_B,
            tipo_procedimiento_id=tipo_id,
            dias_desde_cirugia=7,
            notas="Caso demo B: codigo DEMO2X para emparejamiento en vivo.",
        )
        await _asegurar_vinculo_caso_a(sesion, caso_a.id)
        await _asegurar_codigo_pendiente_caso_b(sesion, caso_b.id, cfg)
        await _asegurar_alerta_urgente_caso_a(sesion, caso_a.id)
        await sesion.commit()

        mensajes.append(f"Caso A: {PACIENTE_DOC_A} ({caso_a.id})")
        mensajes.append(f"Caso B: {PACIENTE_DOC_B} ({caso_b.id}) codigo {CODIGO_EMPAREJAMIENTO_CASO_B}")

    if sembrar_conversacion:
        await _sembrar_conversacion_caso_a(cfg)
        mensajes.append(f"Conversacion sembrada en thread telegram:{CHAT_TELEGRAM_CASO_A}")

    return ResultadoSemillaDemo(
        emails_staff=emails,
        tipo_procedimiento_id=tipo_id,
        caso_a_id=caso_a.id,
        caso_b_id=caso_b.id,
        mensajes=mensajes,
    )
