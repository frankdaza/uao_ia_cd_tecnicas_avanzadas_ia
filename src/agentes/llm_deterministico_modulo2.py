"""
Modelos chat deterministas para ``MOCK_LLM=1`` (E2E y laboratorios sin OpenAI).

El router inspecciona el texto del mensaje humano sintetizado por el grafo (incluye
historial y la consulta actual) y elige ``faq_estructurada`` o ``rag_denso`` segun
tokens magicos documentados en ``scripts/README.md`` (prefijo ``e2e70xx``).
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool


def _texto_ultimo_humano(mensajes: list[BaseMessage]) -> str:
    for m in reversed(mensajes):
        if isinstance(m, HumanMessage):
            c = m.content
            return c if isinstance(c, str) else str(c)
    return ""


def _extraer_consulta_actual(texto_router: str) -> str:
    """Devuelve la linea de la consulta actual o el texto completo."""
    marcador = "Consulta actual del usuario:"
    if marcador in texto_router:
        _, _, resto = texto_router.partition(marcador)
        return resto.strip().lstrip("\n").strip()
    return texto_router.strip()


def _elegir_tool_y_consulta(texto_router: str) -> tuple[str, str]:
    """
    Retorna ``(nombre_tool, consulta_tool)``.

    Tokens (documentados para E2E con ``MOCK_LLM=1``):

    - ``e2e7001`` -> ``rag_denso``
    - ``e2e7002`` -> ``faq_estructurada``
    - ``e2e7003`` -> ``rag_denso`` (turno de continuidad / memoria conversacional)
    """
    consulta = _extraer_consulta_actual(texto_router)
    if "e2e7002" in texto_router:
        return "faq_estructurada", consulta or "faq"
    if "e2e7001" in texto_router or "e2e7003" in texto_router:
        return "rag_denso", consulta or "consulta"
    return "rag_denso", consulta or "consulta"


class RouterDeterministicoModulo2E2e:
    """Sustituto de ``ChatOpenAI`` del router: ``bind_tools().invoke(...)``."""

    def bind_tools(self, tools: list[StructuredTool], **kwargs: Any) -> RouterDeterministicoModulo2E2e._Enlazado:
        _ = kwargs
        return self._Enlazado(tools)

    class _Enlazado:
        def __init__(self, tools: list[StructuredTool]) -> None:
            self._nombres = {t.name for t in tools}

        def invoke(self, mensajes: list[BaseMessage], config: Any = None, **kwargs: Any) -> AIMessage:
            _ = config, kwargs
            texto = _texto_ultimo_humano(list(mensajes))
            tool, consulta = _elegir_tool_y_consulta(texto)
            if tool not in self._nombres:
                tool = "rag_denso"
            args = {"consulta": consulta[:2000]}
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool,
                        "args": args,
                        "id": "call_e2e_mock_router",
                        "type": "tool_call",
                    }
                ],
            )


class CompositorDeterministicoModulo2E2e:
    """Sustituto del compositor: ``stream`` e ``invoke`` sin API externa."""

    def stream(self, mensajes: list[BaseMessage], **kwargs: Any) -> Any:
        _ = kwargs
        texto = _texto_ultimo_humano(list(mensajes))
        sistema = ""
        for m in mensajes:
            if isinstance(m, SystemMessage):
                c = m.content
                sistema += c if isinstance(c, str) else str(c)
        yield AIMessage(content=self._texto_respuesta(texto, sistema))

    def invoke(self, mensajes: list[BaseMessage], **kwargs: Any) -> AIMessage:
        _ = kwargs
        texto = _texto_ultimo_humano(list(mensajes))
        sistema = ""
        for m in mensajes:
            if isinstance(m, SystemMessage):
                c = m.content
                sistema += c if isinstance(c, str) else str(c)
        return AIMessage(content=self._texto_respuesta(texto, sistema))

    @staticmethod
    def _texto_respuesta(ultimo_humano: str, _bloque_sistema: str) -> str:
        t = ultimo_humano.lower()
        if "e2e7003" in ultimo_humano and "color" in t:
            return (
                "En el mensaje anterior indicaste que tu color favorito es azul. "
                "(Respuesta determinista MOCK_LLM.)"
            )
        if "e2e7002" in ultimo_humano:
            if re.search(r"horario|siau|pqrs", t):
                return (
                    "El SIAU atiende en horario institucional de referencia "
                    "(respuesta breve de modo MOCK_LLM; ver JSON FAQ para el detalle exacto)."
                )
            return "Respuesta FAQ sintetica (MOCK_LLM)."
        if "e2e7001" in ultimo_humano:
            return (
                "Resumen institucional simulado: la Fundacion Valle del Lili articula "
                "servicios asistenciales, docencia e investigacion (MOCK_LLM, contexto RAG opcional)."
            )
        return "Respuesta generica del compositor determinista (MOCK_LLM)."


__all__ = [
    "CompositorDeterministicoModulo2E2e",
    "RouterDeterministicoModulo2E2e",
]
