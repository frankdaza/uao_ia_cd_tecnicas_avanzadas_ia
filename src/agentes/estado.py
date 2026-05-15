"""
Estado compartido del grafo LangGraph del agente conversacional (Modulo 2).
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage


class EstadoAgente(TypedDict, total=False):
    """
    Estado de un turno del agente.

    ``pensamientos`` usa reducer por concatenacion para anexar trazas del router
    y pasos intermedios hacia la capa SSE (task-57).
    """

    pregunta: str
    session_id: str
    primer_turno: bool
    usuario: dict[str, Any]
    historial_previo_vacio: bool
    mensajes_historial: list[BaseMessage]
    mensaje_router: AIMessage | None
    intencion: str
    tool_decidida: str | None
    argumentos_tool: dict[str, Any]
    resultado_tool: dict[str, Any]
    fuentes: list[dict[str, Any]]
    pensamientos: Annotated[list[dict[str, Any]], operator.add]
    respuesta_final: str
