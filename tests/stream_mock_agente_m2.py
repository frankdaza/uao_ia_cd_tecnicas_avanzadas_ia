"""Secuencia minima de eventos ``astream_events`` v2 para mocks del endpoint agente."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


async def astream_eventos_agente_minimos(*_a: object, **_k: object) -> Any:
    """
    Compatible con el parser de ``src.api.routers.agente`` (orden feliz corto).

    Emite: pensamiento (decidir_tool), tokens (componer_respuesta), herramienta
    (ejecutar_tool); el endpoint agrega ``final`` al cerrar el iterador.
    """
    yield {
        "event": "on_chain_end",
        "metadata": {"langgraph_node": "decidir_tool"},
        "data": {
            "output": {
                "pensamientos": [
                    {
                        "tipo": "decision_router",
                        "herramienta": "faq_estructurada",
                        "razon_breve": "mock de prueba",
                        "argumentos_resumidos": {},
                    }
                ]
            }
        },
    }
    yield {
        "event": "on_chain_start",
        "metadata": {"langgraph_node": "ejecutar_tool"},
        "data": {},
    }
    yield {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_node": "componer_respuesta"},
        "data": {"chunk": SimpleNamespace(content="Hola ")},
    }
    yield {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_node": "componer_respuesta"},
        "data": {"chunk": SimpleNamespace(content="mock.")},
    }
    yield {
        "event": "on_chain_end",
        "metadata": {"langgraph_node": "ejecutar_tool"},
        "data": {
            "output": {
                "tool_decidida": "faq_estructurada",
                "resultado_tool": {"encontrado": True},
                "fuentes": [],
                "pensamientos": [
                    {
                        "tipo": "ejecucion_tool",
                        "herramienta": "faq_estructurada",
                        "faq_match_encontrado": True,
                        "faq_umbral_match": 0.5,
                        "faq_consulta_ejecutada": "demo",
                    }
                ],
            }
        },
    }
