"""Registro de tools del agente TAAM."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from src.agentes.tools.clasificar_triage import clasificar_triage
from src.agentes.tools.consultar_protocolo_rag import consultar_protocolo_rag
from src.agentes.tools.escalar_a_equipo import escalar_a_equipo
from src.agentes.tools.faq_postoperatorio import faq_postoperatorio
from src.agentes.tools.obtener_contexto_caso import obtener_contexto_caso


def crear_tools_taam() -> list[BaseTool]:
    """Lista de tools con ``name`` en ingles para function calling."""
    return [
        obtener_contexto_caso,
        consultar_protocolo_rag,
        faq_postoperatorio,
        clasificar_triage,
        escalar_a_equipo,
    ]
