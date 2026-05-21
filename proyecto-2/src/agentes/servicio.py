"""Invocacion del agente desde API o integraciones (TASK-104 / 106)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.agente_taam import construir_agente_taam
from src.agentes.contexto import (
    ContextoTaam,
    establecer_contexto_runtime,
    limpiar_contexto_runtime,
)
from src.agentes.tools.resolver_caso import resumen_caso_para_prompt


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

        agente = construir_agente_taam(checkpointer)
        entrada = {"messages": [HumanMessage(content=mensaje)]}
        return await agente.ainvoke(
            entrada,
            config=_config_hilo(session_id),
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
    establecer_contexto_runtime(
        session_id=session_id,
        session_factory=session_factory,
    )
    try:
        async with session_factory() as sesion:
            contexto = await _construir_contexto_invoke(sesion, session_id)

        agente = construir_agente_taam(checkpointer)
        comando = Command(resume={"decisions": [{"type": decision}]})
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
