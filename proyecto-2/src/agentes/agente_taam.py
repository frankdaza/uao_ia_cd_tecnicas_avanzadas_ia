"""Ensamblado del agente TAAM con ``create_agent`` (Ruta A)."""

from __future__ import annotations

from functools import lru_cache

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.agentes.contexto import ContextoTaam
from src.agentes.modelo import crear_modelo_agente
from src.agentes.prompts import prompt_dinamico_taam
from src.agentes.tools.fabrica import crear_tools_taam
from src.configuracion import Configuracion, obtener_configuracion

NOMBRE_TOOL_ESCALAR = "escalar_a_equipo"


def construir_agente_taam(
    checkpointer: BaseCheckpointSaver,
    cfg: Configuracion | None = None,
):
    """
    Agente LangChain con tools estrictas, prompt dinamico y HITL en escalamiento.

    ``HumanInTheLoopMiddleware`` interrumpe antes de ejecutar ``escalar_a_equipo``
    (severidad urgente / red flags UC-MVP-03).
    """
    conf = cfg or obtener_configuracion()
    modelo = crear_modelo_agente(conf)
    tools = crear_tools_taam()
    hitl = HumanInTheLoopMiddleware(
        interrupt_on={
            NOMBRE_TOOL_ESCALAR: {
                "allowed_decisions": ["approve", "reject"],
            },
        },
        description_prefix="Escalamiento clinico pendiente de aprobacion",
    )
    return create_agent(
        modelo,
        tools=tools,
        checkpointer=checkpointer,
        middleware=[prompt_dinamico_taam, hitl],
        context_schema=ContextoTaam,
        name="taam_postoperatorio",
    )


@lru_cache
def obtener_agente_cached(
    url_bd: str,
    cfg_key: str,
) -> object:
    """Cache por URL de BD (tests vs produccion)."""
    from src.agentes.checkpointer import crear_checkpointer_para_url

    cfg = obtener_configuracion()
    cp = crear_checkpointer_para_url(url_bd, cfg)
    return construir_agente_taam(cp, cfg)
