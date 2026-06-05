"""Persistencia automatica de alertas cuando el triage lo requiere."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.agente_taam import NOMBRE_TOOL_ESCALAR
from src.agentes.estado_hitl import hitl_escalar_habilitado_efectivo
from src.agentes.servicio import extraer_severidad_triage, requiere_revision_humana
from src.agentes.tools.clasificar_triage import clasificar_triage
from src.agentes.tools.esquemas import SeveridadTriage
from src.agentes.tools.resolver_caso import resolver_caso_activo_por_session
from src.persistencia.modelos import AlertaTriage
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage

logger = logging.getLogger(__name__)

_SEVERIDADES_CON_ALERTA: frozenset[str] = frozenset({"urgente", "seguimiento"})
_VENTANA_DEDUPE_MIN = 5
_MAX_REF = 1024
_NOMBRE_TOOL_TRIAGE = "clasificar_triage"


def _es_mensaje_tool(msg: object) -> bool:
    tipo = getattr(msg, "type", None) or getattr(msg, "role", None)
    return tipo == "tool"


def _nombre_tool(msg: object) -> str | None:
    nombre = getattr(msg, "name", None)
    return str(nombre) if nombre else None


def _parsear_json_tool(contenido: object) -> dict[str, Any] | None:
    if isinstance(contenido, dict):
        return contenido
    if hasattr(contenido, "model_dump"):
        return contenido.model_dump()
    if isinstance(contenido, str) and contenido.strip():
        try:
            datos = json.loads(contenido)
        except json.JSONDecodeError:
            return None
        return datos if isinstance(datos, dict) else None
    return None


def escalar_creo_alerta_en_turno(estado: dict[str, Any]) -> bool:
    """True si ``escalar_a_equipo`` ya persistio una alerta en este turno."""
    for msg in estado.get("messages", []):
        if not _es_mensaje_tool(msg) or _nombre_tool(msg) != NOMBRE_TOOL_ESCALAR:
            continue
        datos = _parsear_json_tool(getattr(msg, "content", ""))
        if datos and datos.get("alerta_id"):
            return True
    return False


def _rationale_desde_estado(estado: dict[str, Any]) -> str:
    for msg in estado.get("messages", []):
        if not _es_mensaje_tool(msg) or _nombre_tool(msg) != _NOMBRE_TOOL_TRIAGE:
            continue
        datos = _parsear_json_tool(getattr(msg, "content", ""))
        if datos:
            rationale = datos.get("rationale")
            if isinstance(rationale, str) and rationale.strip():
                return rationale.strip()
    return ""


def resolver_severidad_turno(
    estado: dict[str, Any],
    mensaje_paciente: str,
) -> tuple[SeveridadTriage | None, str]:
    """Severidad del turno: tools del agente o heuristica sobre el mensaje."""
    severidad = extraer_severidad_triage(estado)
    rationale = _rationale_desde_estado(estado) if severidad else ""
    if severidad is not None:
        return severidad, rationale or f"Triage {severidad}."

    salida = clasificar_triage.invoke(
        {
            "sintomas_descritos": mensaje_paciente,
            "mensaje_paciente": mensaje_paciente,
        }
    )
    return salida.severidad, salida.rationale


async def _existe_alerta_duplicada(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
    mensaje_ref: str,
) -> bool:
    limite = datetime.now(UTC) - timedelta(minutes=_VENTANA_DEDUPE_MIN)
    stmt = (
        select(AlertaTriage.id)
        .where(
            AlertaTriage.caso_id == caso_id,
            AlertaTriage.mensaje_paciente_ref == mensaje_ref,
            AlertaTriage.created_at >= limite,
        )
        .limit(1)
    )
    res = await sesion.execute(stmt)
    return res.scalars().first() is not None


async def asegurar_alerta_desde_turno(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    session_id: str,
    mensaje_paciente: str,
    estado: dict[str, Any],
) -> uuid.UUID | None:
    """
    Crea fila en ``alertas_triage`` si el triage es urgente/seguimiento y no hay alerta.

    No actua si HITL esta activo y el grafo quedo interrumpido (staff debe aprobar).
    """
    if await hitl_escalar_habilitado_efectivo() and requiere_revision_humana(estado):
        return None
    if escalar_creo_alerta_en_turno(estado):
        return None

    severidad, rationale = resolver_severidad_turno(estado, mensaje_paciente)
    if severidad not in _SEVERIDADES_CON_ALERTA:
        return None

    ref = mensaje_paciente.strip()[:_MAX_REF]
    async with session_factory() as sesion:
        ctx = await resolver_caso_activo_por_session(sesion, session_id)
        if ctx is None:
            logger.warning(
                "auto_alerta_sin_caso session_id=%s severidad=%s",
                session_id,
                severidad,
            )
            return None
        if ref and await _existe_alerta_duplicada(sesion, ctx.caso_id, ref):
            return None

        repo = RepositorioAlertasTriage(sesion)
        resumen = (rationale or f"Sintoma reportado ({severidad})")[:1024]
        try:
            fila = await repo.crear(
                caso_id=ctx.caso_id,
                severidad=severidad,
                resumen=resumen,
                mensaje_paciente_ref=ref or None,
                tool_trace_json={
                    "origen": "auto_triage",
                    "session_id": session_id,
                },
            )
            await sesion.commit()
            logger.info(
                "auto_alerta_creada session_id=%s caso_id=%s alerta_id=%s severidad=%s",
                session_id,
                ctx.caso_id,
                fila.id,
                severidad,
            )
            return fila.id
        except Exception:
            logger.exception("auto_alerta_error session_id=%s", session_id)
            await sesion.rollback()
            return None
