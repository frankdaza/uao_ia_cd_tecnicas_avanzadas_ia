"""Pruebas del grafo LangGraph del router (FakeListChatModel / dobles sin OpenAI)."""

from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from src.agentes.herramientas.faq_tool import ArgsConsultaFaq
from src.agentes.herramientas.rag_tool import ArgsConsultaRagDenso
from src.agentes.meta_prompt import MetaPromptConfig
from src.agentes.router import crear_grafo_agente


def _meta_prompt_minimo() -> MetaPromptConfig:
    return MetaPromptConfig.model_validate(
        {
            "version": 1,
            "modelo_router": "gpt-4o-mini",
            "system_prompt": (
                "Eres el router. No emitas texto libre: solo tool-calls. "
                "Elige faq_estructurada para datos puntuales y rag_denso para corpus amplio. "
                "Instrucciones sinteticas para pruebas." + ("x" * 40)
            ),
            "herramientas": [
                {
                    "name": "faq_estructurada",
                    "description": "FAQ JSON determinista.",
                    "when_to_use": "Datos puntuales institucionales.",
                    "ejemplos": ["Telefono PBX"],
                },
                {
                    "name": "rag_denso",
                    "description": "RAG denso Qdrant.",
                    "when_to_use": "Consultas abiertas sobre documentacion.",
                    "ejemplos": ["Politica de calidad"],
                },
            ],
            "reglas_decision": ["Priorizar FAQ cuando aplique match directo."],
            "respuesta_sin_contexto": "No tengo información suficiente",
            "saludo_template": "Hola {nombre}, bienvenido.",
        }
    )


class _ListaRouterFalso:
    """Doble ligero con ``bind_tools().invoke()`` (``FakeListChatModel`` no implementa bind_tools)."""

    def __init__(self, respuestas: list[AIMessage]) -> None:
        self.respuestas = respuestas
        self.indice = 0

    def bind_tools(self, tools: Any, **kwargs: Any) -> _ListaRouterFalso._Enlazado:
        return self._Enlazado(self)

    class _Enlazado:
        def __init__(self, padre: _ListaRouterFalso) -> None:
            self._padre = padre

        def invoke(self, mensajes: Any, config: Any = None, **kwargs: Any) -> AIMessage:
            i = self._padre.indice
            self._padre.indice += 1
            return self._padre.respuestas[min(i, len(self._padre.respuestas) - 1)]


class _MemoriaFalsa:
    def __init__(self, historial_previo: list[Any] | None = None) -> None:
        self.historial = list(historial_previo or [])
        self.agregar_humano_calls: list[str] = []
        self.agregar_ai_calls: list[tuple[str, dict[str, Any] | None]] = []

    def cargar_ventana(
        self,
        dias_max: int | None = None,
        turnos_max: int | None = None,
    ) -> list[Any]:
        _ = dias_max, turnos_max
        return list(self.historial)

    def agregar_humano(self, texto: str) -> None:
        self.agregar_humano_calls.append(texto)

    def agregar_ai(self, texto: str, metadata: dict[str, Any] | None = None) -> None:
        self.agregar_ai_calls.append((texto, metadata))


def _tool_faq_falsa() -> StructuredTool:
    def _ejecutar(consulta: str) -> dict[str, Any]:
        """Responde FAQ sintetica."""
        _ = consulta
        return {"encontrado": True, "respuesta": "Linea PBX de prueba 018000-111-222."}

    return StructuredTool.from_function(
        name="faq_estructurada",
        description="FAQ falsa para pruebas unitarias.",
        func=_ejecutar,
        args_schema=ArgsConsultaFaq,
        infer_schema=False,
    )


def _tool_rag_falsa() -> StructuredTool:
    def _ejecutar(consulta: str) -> dict[str, Any]:
        """Devuelve fuentes ficticias tipo salida RAG densa."""
        _ = consulta
        return {
            "respuesta_contexto": "[CHUNK 0] titulo: Politica\nURL: https://ejemplo.test/p\n\nTexto.",
            "fuentes": [
                {
                    "archivo": "politica.md",
                    "titulo": "Politica",
                    "source_url": "https://ejemplo.test/p",
                    "score": 0.91,
                    "chunk_index": 0,
                }
            ],
        }

    return StructuredTool.from_function(
        name="rag_denso",
        description="RAG falso para pruebas unitarias.",
        func=_ejecutar,
        args_schema=ArgsConsultaRagDenso,
        infer_schema=False,
    )


@pytest.fixture
def herramientas_falsas() -> tuple[StructuredTool, StructuredTool]:
    return (_tool_faq_falsa(), _tool_rag_falsa())


def test_import_router_no_carga_recuperador_bm25() -> None:
    codigo = Path("src/agentes/router.py").read_text(encoding="utf-8")
    assert "src.retrieval" not in codigo
    assert "recuperador" not in codigo


def test_grafo_turno_completo_faq_fake_models(
    herramientas_falsas: tuple[StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t = herramientas_falsas
    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "faq_estructurada",
                        "args": {"consulta": "telefono PBX"},
                        "id": "call_faq",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor = FakeListChatModel(responses=["Respuesta final del compositor (FAQ)."])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )
    memoria = _MemoriaFalsa()
    salida = grafo.invoke(
        {
            "pregunta": "Cual es el telefono?",
            "session_id": "user:00000000-0000-4000-8000-000000000001",
            "primer_turno": True,
            "usuario": {"nombre": "Laura", "doc_id": "999"},
        },
        config={"configurable": {"memoria": memoria}},
    )
    assert salida["respuesta_final"] == "Respuesta final del compositor (FAQ)."
    assert salida["tool_decidida"] == "faq_estructurada"
    assert salida["fuentes"] == []
    assert memoria.agregar_humano_calls == ["Cual es el telefono?"]
    assert len(memoria.agregar_ai_calls) == 1
    meta = memoria.agregar_ai_calls[0][1] or {}
    assert meta.get("tool") == "faq_estructurada"
    tipos = [p["tipo"] for p in salida.get("pensamientos") or []]
    assert "decision_router" in tipos
    assert "ejecucion_tool" in tipos


def test_grafo_rama_rag_y_fuentes_en_estado(
    herramientas_falsas: tuple[StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t = herramientas_falsas
    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "rag_denso",
                        "args": {"consulta": "politica institucional"},
                        "id": "call_rag",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor = FakeListChatModel(responses=["Respuesta con contexto RAG."])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )
    memoria = _MemoriaFalsa()
    salida = grafo.invoke(
        {
            "pregunta": "Explique la politica",
            "session_id": "user:00000000-0000-4000-8000-000000000002",
            "primer_turno": False,
            "usuario": {"nombre": "Carlos", "doc_id": "1"},
        },
        config={"configurable": {"memoria": memoria}},
    )
    assert salida["tool_decidida"] == "rag_denso"
    assert len(salida.get("fuentes") or []) == 1
    assert salida["fuentes"][0].get("archivo") == "politica.md"


def test_astream_events_smoke(
    herramientas_falsas: tuple[StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t = herramientas_falsas
    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "faq_estructurada",
                        "args": {"consulta": "x"},
                        "id": "c1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor = FakeListChatModel(responses=["OK"])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )

    async def _recolectar() -> list[str]:
        eventos: list[str] = []
        async for ev in grafo.astream_events(
            {
                "pregunta": "P",
                "session_id": "user:00000000-0000-4000-8000-000000000003",
                "primer_turno": False,
                "usuario": {},
            },
            version="v2",
            config={"configurable": {"memoria": _MemoriaFalsa()}},
        ):
            eventos.append(ev.get("event", ""))
        return eventos

    eventos = asyncio.run(_recolectar())
    assert "on_chain_start" in eventos
    assert len(eventos) >= 3


def test_pensamiento_router_incluye_herramienta(
    herramientas_falsas: tuple[StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t = herramientas_falsas
    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "rag_denso",
                        "args": {"consulta": "abc"},
                        "id": "c2",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor = FakeListChatModel(responses=["Z"])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )
    salida = grafo.invoke(
        {
            "pregunta": "Q",
            "session_id": "user:00000000-0000-4000-8000-000000000004",
            "primer_turno": False,
            "usuario": {},
        },
        config={"configurable": {"memoria": _MemoriaFalsa()}},
    )
    decisiones = [p for p in salida.get("pensamientos") or [] if p.get("tipo") == "decision_router"]
    assert decisiones and decisiones[0].get("herramienta") == "rag_denso"


def test_modulo_prompt_no_carga_legacy_ni_rank_bm25() -> None:
    """Import frio de prompt: no debe arrastrar modulos BM25 eliminados."""
    sys.modules.pop("src.qa.prompt", None)
    for k in list(sys.modules):
        if k.startswith("src.legacy") or k == "rank_bm25":
            del sys.modules[k]
    prompt_modulo = importlib.import_module("src.qa.prompt")
    assert "No tengo información suficiente" in prompt_modulo.PROMPT_SISTEMA_DEFECTO
    assert not any(m.startswith("src.legacy") for m in sys.modules)
    assert "rank_bm25" not in sys.modules
