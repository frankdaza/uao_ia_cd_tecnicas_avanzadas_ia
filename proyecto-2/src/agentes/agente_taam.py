"""Ensamblado del agente TAAM con ``create_agent`` (Ruta A)."""

from __future__ import annotations

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
    *,
    hitl_escalar_habilitado: bool | None = None,
):
    """
    Agente LangChain con tools estrictas, prompt dinamico y HITL opcional en escalamiento.

    Con ``hitl_escalar_habilitado=true``, ``HumanInTheLoopMiddleware`` interrumpe
    antes de ejecutar ``escalar_a_equipo`` (UC-MVP-03). Por defecto el escalamiento
    persiste la alerta sin interrupcion.
    """
    conf = cfg or obtener_configuracion()
    usar_hitl = (
        conf.agente_hitl_escalar_habilitado
        if hitl_escalar_habilitado is None
        else hitl_escalar_habilitado
    )
    modelo = crear_modelo_agente(conf)
    tools = crear_tools_taam()
    middleware: list = [prompt_dinamico_taam]
    if usar_hitl:
        hitl = HumanInTheLoopMiddleware(
            interrupt_on={
                NOMBRE_TOOL_ESCALAR: {
                    "allowed_decisions": ["approve", "reject"],
                },
            },
            description_prefix="Escalamiento clinico pendiente de aprobacion",
        )
        middleware.append(hitl)
    return create_agent(
        modelo,
        tools=tools,
        checkpointer=checkpointer,
        middleware=middleware,
        context_schema=ContextoTaam,
        name="taam_postoperatorio",
    )
