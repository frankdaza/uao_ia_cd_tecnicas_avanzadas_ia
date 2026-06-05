"""Invocacion del agente desde API o integraciones (TASK-104 / 106)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.agente_taam import construir_agente_taam
from src.agentes.contexto import (
    ContextoTaam,
    establecer_contexto_runtime,
    limpiar_contexto_runtime,
)
from src.agentes.guardrails_alcance import (
    MENSAJE_FUERA_DE_ALCANCE,
    evaluar_alcance_consulta,
)
from src.agentes.tools.esquemas import SeveridadTriage
from src.agentes.tools.resolver_caso import resumen_caso_para_prompt
from src.configuracion import obtener_configuracion

_RE_FRAGMENTO_RAG = re.compile(r"^\[(\d+)\]\s*(.+)$", re.MULTILINE)
_NOMBRE_TOOL_TRIAGE = "clasificar_triage"
_NOMBRE_TOOL_RAG = "consultar_protocolo_rag"
_SEVERIDADES_VALIDAS: frozenset[str] = frozenset({"info", "seguimiento", "urgente"})
_DECISIONES_HITL: frozenset[str] = frozenset({"approve", "reject"})

logger = logging.getLogger(__name__)


def _config_hilo(session_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def requiere_revision_humana(estado: dict[str, Any]) -> bool:
    """True si el grafo quedo en interrupcion HITL (``__interrupt__``)."""
    return bool(estado.get("__interrupt__"))


async def _construir_contexto_invoke(
    sesion: AsyncSession,
    session_id: str,
) -> ContextoTaam:
    resumen = await resumen_caso_para_prompt(sesion, session_id)
    ctx: ContextoTaam = {"session_id": session_id}
    if resumen:
        ctx["resumen_caso"] = resumen
    else:
        ctx["sin_vinculo"] = True
    return ctx


def _normalizar_decision_hitl(decision: str) -> str:
    valor = decision.strip().lower()
    if valor not in _DECISIONES_HITL:
        raise ValueError(f"decision HITL invalida: {decision!r}")
    return valor


async def _persistir_rechazo_alcance(
    agente: object,
    *,
    config: dict[str, Any],
    mensaje: str,
) -> dict[str, Any]:
    """Registra turno humano + rechazo fijo en el checkpointer sin invocar el LLM del agente."""
    snap = await agente.aget_state(config)  # type: ignore[attr-defined]
    previos: list[object] = []
    if snap is not None and snap.values:
        previos = list(snap.values.get("messages", []))
    nuevos = previos + [
        HumanMessage(content=mensaje),
        AIMessage(content=MENSAJE_FUERA_DE_ALCANCE),
    ]
    await agente.aupdate_state(config, {"messages": nuevos})  # type: ignore[attr-defined]
    return {"messages": nuevos}


async def reanudar_hitl_si_pendiente(
    agente: object,
    *,
    session_id: str,
    contexto: ContextoTaam,
    decision: str = "reject",
) -> dict[str, Any] | None:
    """
    Si el hilo tiene nodos pendientes (p. ej. HITL en ``escalar_a_equipo``), reanuda el grafo.

    Evita enviar un ``HumanMessage`` nuevo sobre un ``tool_call`` sin ``ToolMessage``,
    que OpenAI rechaza con 400.
    """
    config = _config_hilo(session_id)
    snap = await agente.aget_state(config)  # type: ignore[attr-defined]
    if snap is None or not snap.next:
        return None

    decision_norm = _normalizar_decision_hitl(decision)
    logger.info(
        "hitl_reanudacion session_id=%s decision=%s",
        session_id,
        decision_norm,
    )
    comando = Command(resume={"decisions": [{"type": decision_norm}]})
    return await agente.ainvoke(  # type: ignore[attr-defined]
        comando,
        config=config,
        context=contexto,
    )


async def invocar_agente(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    session_id: str,
    mensaje: str,
) -> dict[str, Any]:
    """
    Un turno del agente. Devuelve el estado del grafo (incluye ``__interrupt__`` si HITL).
    """
    establecer_contexto_runtime(
        session_id=session_id,
        session_factory=session_factory,
    )
    try:
        async with session_factory() as sesion:
            contexto = await _construir_contexto_invoke(sesion, session_id)

        conf = obtener_configuracion()
        agente = construir_agente_taam(checkpointer)
        config = _config_hilo(session_id)
        await reanudar_hitl_si_pendiente(
            agente,
            session_id=session_id,
            contexto=contexto,
            decision="reject",
        )
        alcance = await evaluar_alcance_consulta(mensaje, conf)
        if not alcance.en_alcance:
            logger.info(
                "guardrail_fuera_alcance session_id=%s motivo=%s",
                session_id,
                alcance.motivo,
            )
            return await _persistir_rechazo_alcance(
                agente,
                config=config,
                mensaje=mensaje,
            )
        entrada = {"messages": [HumanMessage(content=mensaje)]}
        return await agente.ainvoke(
            entrada,
            config=config,
            context=contexto,
        )
    finally:
        limpiar_contexto_runtime()


async def continuar_despues_hitl(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    session_id: str,
    decision: str = "approve",
) -> dict[str, Any]:
    """
    Reanuda el grafo tras HITL (p. ej. staff aprueba ``escalar_a_equipo``).

    ``decision``: ``approve`` o ``reject`` segun documentacion LangChain HITL.
    """
    decision_norm = _normalizar_decision_hitl(decision)
    establecer_contexto_runtime(
        session_id=session_id,
        session_factory=session_factory,
    )
    try:
        async with session_factory() as sesion:
            contexto = await _construir_contexto_invoke(sesion, session_id)

        agente = construir_agente_taam(checkpointer)
        comando = Command(resume={"decisions": [{"type": decision_norm}]})
        return await agente.ainvoke(
            comando,
            config=_config_hilo(session_id),
            context=contexto,
        )
    finally:
        limpiar_contexto_runtime()


def extraer_texto_respuesta(estado: dict[str, Any]) -> str:
    """Ultimo mensaje AI del estado, o mensaje fijo si hay interrupcion."""
    if requiere_revision_humana(estado):
        return (
            "Su consulta fue registrada y sera revisada por el equipo clinico en breve. "
            "Si tiene una emergencia, acuda a urgencias de inmediato."
        )
    mensajes = estado.get("messages", [])
    for msg in reversed(mensajes):
        tipo = getattr(msg, "type", None) or getattr(msg, "role", None)
        if tipo in ("ai", "assistant"):
            contenido = getattr(msg, "content", "")
            if isinstance(contenido, str) and contenido.strip():
                return contenido.strip()
            if isinstance(contenido, list):
                textos = [
                    bloque.get("text", "")
                    for bloque in contenido
                    if isinstance(bloque, dict) and bloque.get("type") == "text"
                ]
                unido = " ".join(t for t in textos if t).strip()
                if unido:
                    return unido
    return (
        "Gracias por su mensaje. En este momento no pudimos generar una respuesta; "
        "el equipo de seguimiento lo atendera pronto."
    )


def _es_mensaje_tool(msg: object) -> bool:
    tipo = getattr(msg, "type", None) or getattr(msg, "role", None)
    return tipo == "tool"


def _nombre_tool(msg: object) -> str | None:
    nombre = getattr(msg, "name", None)
    return str(nombre) if nombre else None


def _parsear_severidad_desde_contenido(contenido: object) -> SeveridadTriage | None:
    if isinstance(contenido, dict):
        valor = contenido.get("severidad")
        if isinstance(valor, str) and valor in _SEVERIDADES_VALIDAS:
            return valor  # type: ignore[return-value]
    if hasattr(contenido, "severidad"):
        valor = getattr(contenido, "severidad", None)
        if isinstance(valor, str) and valor in _SEVERIDADES_VALIDAS:
            return valor  # type: ignore[return-value]
    if isinstance(contenido, str):
        texto = contenido.strip()
        if not texto:
            return None
        try:
            datos = json.loads(texto)
        except json.JSONDecodeError:
            return None
        if isinstance(datos, dict):
            valor = datos.get("severidad")
            if isinstance(valor, str) and valor in _SEVERIDADES_VALIDAS:
                return valor  # type: ignore[return-value]
    return None


def extraer_severidad_triage(estado: dict[str, Any]) -> SeveridadTriage | None:
    """Ultima severidad emitida por ``clasificar_triage`` en el turno."""
    severidad: SeveridadTriage | None = None
    for msg in estado.get("messages", []):
        if not _es_mensaje_tool(msg) or _nombre_tool(msg) != _NOMBRE_TOOL_TRIAGE:
            continue
        parsed = _parsear_severidad_desde_contenido(getattr(msg, "content", ""))
        if parsed is not None:
            severidad = parsed
    return severidad


def extraer_fuentes_respuesta(
    estado: dict[str, Any],
    *,
    max_fuentes: int = 4,
) -> list[dict[str, str]]:
    """Fragmentos RAG del ultimo ``consultar_protocolo_rag`` con formato ``[n] texto``."""
    for msg in reversed(estado.get("messages", [])):
        if not _es_mensaje_tool(msg) or _nombre_tool(msg) != _NOMBRE_TOOL_RAG:
            continue
        contenido = getattr(msg, "content", "")
        if not isinstance(contenido, str) or not contenido.strip():
            continue
        fuentes: list[dict[str, str]] = []
        for linea in contenido.splitlines():
            coincidencia = _RE_FRAGMENTO_RAG.match(linea.strip())
            if coincidencia:
                fuentes.append(
                    {
                        "titulo": f"Protocolo [{coincidencia.group(1)}]",
                        "fragmento": coincidencia.group(2).strip(),
                    }
                )
        if fuentes:
            return fuentes[:max_fuentes]
    return []
