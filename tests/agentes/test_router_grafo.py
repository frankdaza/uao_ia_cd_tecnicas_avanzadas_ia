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
                {
                    "name": "listar_estructurado",
                    "description": "Listado por payload Qdrant.",
                    "when_to_use": "Enumeracion o conteo por filtros.",
                    "ejemplos": ["Cuantos pediatras hay"],
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
    def _ejecutar(consulta: str, filtros_tipo_pagina: list[str] | None = None) -> dict[str, Any]:
        """Devuelve fuentes ficticias tipo salida RAG densa."""
        _ = consulta, filtros_tipo_pagina
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


def _tool_listar_falsa() -> StructuredTool:
    from src.agentes.herramientas.listar_estructurado_tool import ArgsConsultaListados

    def _ejecutar(
        tipo_pagina: str | None = None,
        especialidad: str | None = None,
        sedes: list[str] | None = None,
        especialidad_contains: str | None = None,
        limite: int = 50,
    ) -> dict[str, Any]:
        _ = tipo_pagina, especialidad, sedes, especialidad_contains, limite
        return {
            "conteo": 2,
            "items": [
                {
                    "nombre": "Dr. Demo",
                    "source_url": "https://ejemplo.test/m",
                    "especialidad": ["Pediatria"],
                    "sedes": ["Sede Valle del Lili"],
                    "archivo": "directorio-medico-x.md",
                }
            ],
            "muestra_truncada": False,
            "filtros_aplicados": {"tipo_pagina": "ficha_medico"},
        }

    return StructuredTool.from_function(
        name="listar_estructurado",
        description="Listado falso para pruebas.",
        func=_ejecutar,
        args_schema=ArgsConsultaListados,
        infer_schema=False,
    )


@pytest.fixture
def herramientas_falsas() -> tuple[StructuredTool, StructuredTool, StructuredTool]:
    return (_tool_faq_falsa(), _tool_rag_falsa(), _tool_listar_falsa())


def test_import_router_no_carga_recuperador_bm25() -> None:
    codigo = Path("src/agentes/router.py").read_text(encoding="utf-8")
    assert "src.retrieval" not in codigo
    assert "recuperador" not in codigo


def test_grafo_turno_completo_faq_fake_models(
    herramientas_falsas: tuple[StructuredTool, StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t, list_t = herramientas_falsas
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
        herramientas=[faq_t, rag_t, list_t],
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
    herramientas_falsas: tuple[StructuredTool, StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t, list_t = herramientas_falsas
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
        herramientas=[faq_t, rag_t, list_t],
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
    herramientas_falsas: tuple[StructuredTool, StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t, list_t = herramientas_falsas
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
        herramientas=[faq_t, rag_t, list_t],
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
    herramientas_falsas: tuple[StructuredTool, StructuredTool, StructuredTool],
) -> None:
    faq_t, rag_t, list_t = herramientas_falsas
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
        herramientas=[faq_t, rag_t, list_t],
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


def test_compositor_recibe_nombre_registrado_e_historial_en_system(
    herramientas_falsas: tuple[StructuredTool, StructuredTool, StructuredTool],
) -> None:
    """El compositor debe ver nombre de sesion y turnos previos en el system prompt."""
    from langchain_core.messages import HumanMessage as HM

    from src.agentes.prompt_institucional import PROMPT_SISTEMA_DEFECTO
    from src.agentes.runtime_agente import RuntimeAgenteBundle

    faq_t, rag_t, list_t = herramientas_falsas
    mem = _MemoriaFalsa(
        [
            HM(content="En el chat digo que me dicen Pepe."),
            AIMessage(content="Entendido."),
        ]
    )
    captura_mensajes: list[list[Any]] = []

    class _CompositorCaptura(FakeListChatModel):
        def stream(self, input, config=None, **kwargs):  # noqa: ANN001, ARG002
            captura_mensajes.append(list(input))
            yield from super().stream(input, config=config, **kwargs)

    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "faq_estructurada",
                        "args": {"consulta": "x"},
                        "id": "c-faq",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor_llm = _CompositorCaptura(responses=["Respuesta breve de prueba."])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor_llm,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t, list_t],
    )
    bundle = RuntimeAgenteBundle(
        llm_router=router_llm,
        llm_compositor=compositor_llm,
        meta_prompt=_meta_prompt_minimo(),
        prompt_institucional=PROMPT_SISTEMA_DEFECTO.rstrip(),
        etiqueta_modelo_compositor="test",
        historial_turnos_max=12,
        rag_top_k=5,
        rag_score_minimo=0.25,
    )
    salida = grafo.invoke(
        {
            "pregunta": "Recuerdas lo anterior?",
            "session_id": "user:00000000-0000-4000-8000-0000000000aa",
            "primer_turno": False,
            "usuario": {"nombre": "Alvaro", "doc_id": "1"},
        },
        config={"configurable": {"memoria": mem, "runtime_agente": bundle}},
    )
    assert salida.get("respuesta_final")
    assert captura_mensajes, "el compositor debio recibir mensajes"
    ultimo = captura_mensajes[-1]
    from langchain_core.messages import SystemMessage

    textos_sistema = [m.content for m in ultimo if isinstance(m, SystemMessage) and isinstance(m.content, str)]
    unido = "\n".join(textos_sistema)
    assert "Alvaro" in unido
    assert "Pepe" in unido


def test_router_system_prompt_incluye_reglas_y_catalogo_herramientas() -> None:
    """reglas_decision y herramientas del meta deben llegar al SystemMessage del router."""
    from langchain_core.messages import SystemMessage

    faq_t, rag_t, list_t = _tool_faq_falsa(), _tool_rag_falsa(), _tool_listar_falsa()
    mensajes_capturados: list[list[Any]] = []
    tools_capturadas: list[list[Any]] = []

    class _RouterCap:
        def __init__(self) -> None:
            self._respuesta = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "faq_estructurada",
                        "args": {"consulta": "x"},
                        "id": "c",
                        "type": "tool_call",
                    }
                ],
            )

        def bind_tools(self, tools_arg: Any, **kwargs: Any) -> Any:
            _ = kwargs
            tools_capturadas.append(list(tools_arg))

            class _E:
                def invoke(self2: Any, mensajes: Any, config: Any = None, **kw: Any) -> AIMessage:
                    _ = self2, config, kw
                    mensajes_capturados.append(list(mensajes))
                    return self._respuesta

            return _E()

    meta = _meta_prompt_minimo()
    grafo = crear_grafo_agente(
        llm_router=_RouterCap(),
        llm_compositor=FakeListChatModel(responses=["ok"]),
        meta_prompt=meta,
        herramientas=[faq_t, rag_t, list_t],
    )
    grafo.invoke(
        {"pregunta": "PBX?", "session_id": "u:1", "primer_turno": True, "usuario": {}},
        config={"configurable": {"memoria": _MemoriaFalsa()}},
    )
    assert mensajes_capturados
    sys_msgs = [m for m in mensajes_capturados[-1] if isinstance(m, SystemMessage)]
    texto = sys_msgs[0].content if sys_msgs and isinstance(sys_msgs[0].content, str) else ""
    assert "Priorizar FAQ cuando aplique match directo." in texto
    assert "Telefono PBX" in texto
    assert "### Herramienta `faq_estructurada`" in texto
    assert "### Herramienta `listar_estructurado`" in texto
    assert tools_capturadas
    d0 = tools_capturadas[-1][0].description
    assert "Telefono PBX" in d0
    assert "Datos puntuales institucionales." in d0


def test_router_system_texto_incluye_solo_reglas_cuando_se_actualiza_lista() -> None:
    """Cambiar solo reglas_decision debe reflejarse en el system del router (paridad JSON admin)."""
    from langchain_core.messages import SystemMessage

    base = _meta_prompt_minimo().model_dump()
    base["reglas_decision"] = ["REGLA_UNICA_ADMIN_SOLO_EN_LISTA."]
    meta = MetaPromptConfig.model_validate(base)

    faq_t, rag_t, list_t = _tool_faq_falsa(), _tool_rag_falsa(), _tool_listar_falsa()
    cap: list[str] = []

    class _RouterCap:
        def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
            _ = kwargs

            class _E:
                def invoke(self2: Any, mensajes: Any, config: Any = None, **kw: Any) -> AIMessage:
                    _ = self2, config, kw
                    for m in mensajes:
                        if isinstance(m, SystemMessage) and isinstance(m.content, str):
                            cap.append(m.content)
                    return AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "faq_estructurada",
                                "args": {"consulta": "x"},
                                "id": "i",
                                "type": "tool_call",
                            }
                        ],
                    )

            return _E()

    grafo = crear_grafo_agente(
        llm_router=_RouterCap(),
        llm_compositor=FakeListChatModel(responses=["x"]),
        meta_prompt=meta,
        herramientas=[faq_t, rag_t, list_t],
    )
    grafo.invoke(
        {"pregunta": "x", "session_id": "u:1", "primer_turno": False, "usuario": {}},
        config={"configurable": {"memoria": _MemoriaFalsa()}},
    )
    assert cap and "REGLA_UNICA_ADMIN_SOLO_EN_LISTA." in cap[-1]


def test_grafo_conteo_pediatras_enruta_listar_sin_llm_router(
    herramientas_falsas: tuple[StructuredTool, StructuredTool, StructuredTool],
) -> None:
    """Heuristica de intencion + filtros: no se invoca al modelo del router."""
    faq_t, rag_t, list_t = herramientas_falsas

    class _RouterProhibido:
        def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
            _ = tools, kwargs

            class _E:
                def invoke(self2: Any, mensajes: Any, config: Any = None, **kw: Any) -> AIMessage:
                    _ = self2, mensajes, config, kw
                    raise AssertionError("No se esperaba invocacion al LLM del router")

            return _E()

    compositor = FakeListChatModel(responses=["Respuesta sintetica al listado."])
    grafo = crear_grafo_agente(
        llm_router=_RouterProhibido(),
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t, list_t],
    )
    salida = grafo.invoke(
        {
            "pregunta": "¿Cuántos pediatras hay en el directorio médico?",
            "session_id": "user:00000000-0000-4000-8000-00000000b701",
            "primer_turno": False,
            "usuario": {},
        },
        config={"configurable": {"memoria": _MemoriaFalsa()}},
    )
    assert salida.get("tool_decidida") == "listar_estructurado"
    rt = salida.get("resultado_tool") or {}
    assert int(rt.get("conteo") or 0) == 2


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
