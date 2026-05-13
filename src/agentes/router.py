"""
Grafo LangGraph (StateGraph) del agente: memoria, tool-calling, composicion Lili y persistencia.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agentes.estado import EstadoAgente
from src.agentes.meta_prompt import MetaPromptConfig
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO

logger = logging.getLogger(__name__)

CLAVE_MEMORIA_EN_CONFIG: str = "memoria"

_NOMBRES_TOOLS_OBLIGATORIAS: frozenset[str] = frozenset({"faq_estructurada", "rag_denso"})


def _texto_mensaje(mensaje: BaseMessage) -> str:
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    return str(contenido)


def _historial_a_texto_router(mensajes: list[BaseMessage], *, max_bloques: int = 24) -> str:
    """Resume el historial en texto plano para el mensaje humano del router."""
    if not mensajes:
        return "(sin mensajes previos en esta sesion)"
    lineas: list[str] = []
    for m in mensajes[-max_bloques:]:
        if isinstance(m, HumanMessage):
            lineas.append(f"usuario: {_texto_mensaje(m)[:1800]}")
        elif isinstance(m, AIMessage):
            lineas.append(f"asistente: {_texto_mensaje(m)[:1800]}")
    return "\n".join(lineas) if lineas else "(sin mensajes previos en esta sesion)"


def _obtener_memoria_desde_config(config: RunnableConfig) -> Any:
    configurable = config.get("configurable") or {}
    mem = configurable.get(CLAVE_MEMORIA_EN_CONFIG)
    if mem is None:
        msg = (
            f"Debe pasarse config['configurable']['{CLAVE_MEMORIA_EN_CONFIG}'] al invocar "
            "el grafo (instancia compatible con cargar_ventana / agregar_humano / agregar_ai)."
        )
        raise ValueError(msg)
    return mem


def _argumentos_serializables(argumentos: dict[str, Any]) -> dict[str, Any]:
    """Evita volcar textos enormes en ``pensamientos``."""
    salida: dict[str, Any] = {}
    for clave, valor in argumentos.items():
        if isinstance(valor, str):
            salida[clave] = valor if len(valor) <= 400 else valor[:400] + "…"
        else:
            salida[clave] = valor
    return salida


def crear_grafo_agente(
    *,
    llm_router: Any,
    llm_compositor: BaseChatModel,
    meta_prompt: MetaPromptConfig,
    herramientas: Sequence[StructuredTool] | None = None,
    prompt_sistema_institucional: str | None = None,
) -> CompiledStateGraph:
    """
    Compila el StateGraph del agente con dependencias inyectadas.

    Parameters
    ----------
    llm_router:
        Modelo chat con ``bind_tools`` (p. ej. ``ChatOpenAI``). En pruebas puede
        sustituirse por un doble que exponga ``bind_tools(...).invoke(...)``.
    llm_compositor:
        Modelo chat para la respuesta final institucional (politica Lili).
    meta_prompt:
        Configuracion validada del JSON del router (system prompt de decision).
    herramientas:
        Tools enlazadas al router; por defecto ``faq_estructurada`` + ``rag_denso``.
    prompt_sistema_institucional:
        Texto base Lili; por defecto :data:`src.qa.prompt.PROMPT_SISTEMA_DEFECTO`.

    Returns
    -------
    CompiledStateGraph
        Grafo compilado. Invocacion tipica::

            grafo.invoke(
                {
                    "pregunta": "...",
                    "session_id": "user:...",
                    "primer_turno": True,
                    "usuario": {"nombre": "Ana", "doc_id": "123"},
                },
                config={"configurable": {"memoria": memoria_usuario}},
            )

    Notes
    -----
    Cancelacion y SSE token a token: usar ``astream_events`` sobre el grafo compilado
    (task-57). La memoria debe exponer ``cargar_ventana``, ``agregar_humano`` y
    ``agregar_ai`` como :class:`src.agentes.memoria.historial.MemoriaUsuario`.
    """
    if herramientas is not None:
        tools = list(herramientas)
    else:
        from src.agentes.herramientas.faq_tool import crear_faq_tool
        from src.agentes.herramientas.rag_tool import crear_rag_tool

        tools = [crear_faq_tool(), crear_rag_tool()]
    nombres = {t.name for t in tools}
    if not _NOMBRES_TOOLS_OBLIGATORIAS.issubset(nombres):
        msg = (
            "``herramientas`` debe incluir al menos las tools "
            f"{sorted(_NOMBRES_TOOLS_OBLIGATORIAS)} (recibido: {sorted(nombres)})."
        )
        raise ValueError(msg)
    tools_por_nombre: dict[str, StructuredTool] = {t.name: t for t in tools}
    texto_institucional = (prompt_sistema_institucional or PROMPT_SISTEMA_DEFECTO).rstrip()

    def nodo_cargar_memoria(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        memoria = _obtener_memoria_desde_config(config)
        mensajes = memoria.cargar_ventana()
        historial_previo_vacio = len(mensajes) == 0
        return {
            "mensajes_historial": mensajes,
            "historial_previo_vacio": historial_previo_vacio,
        }

    def nodo_decidir_tool(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        _ = config
        historial_txt = _historial_a_texto_router(state.get("mensajes_historial") or [])
        contenido_humano = (
            f"{historial_txt}\n\n---\n\nConsulta actual del usuario:\n{state['pregunta']}"
        )
        mensajes_router: list[BaseMessage] = [
            SystemMessage(content=meta_prompt.system_prompt),
            HumanMessage(content=contenido_humano),
        ]
        enlazado = llm_router.bind_tools(tools)
        mensaje_ai: AIMessage = enlazado.invoke(mensajes_router)
        tool_decidida: str | None = None
        argumentos_tool: dict[str, Any] = {}
        if mensaje_ai.tool_calls:
            principal = mensaje_ai.tool_calls[0]
            tool_decidida = principal["name"]
            argumentos_tool = dict(principal.get("args") or {})
        else:
            logger.warning(
                "El router no devolvio tool_calls; se usa rag_denso como respaldo deterministico."
            )
            tool_decidida = "rag_denso"
            argumentos_tool = {"consulta": state["pregunta"]}
        pensamiento = {
            "tipo": "decision_router",
            "herramienta": tool_decidida,
            "razon_breve": "Seleccion vía tool binding del LLM del router segun meta-prompt.",
            "argumentos_resumidos": _argumentos_serializables(argumentos_tool),
        }
        return {
            "mensaje_router": mensaje_ai,
            "tool_decidida": tool_decidida,
            "argumentos_tool": argumentos_tool,
            "pensamientos": [pensamiento],
        }

    def nodo_ejecutar_tool(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        _ = config
        nombre_tool = state.get("tool_decidida") or ""
        args = state.get("argumentos_tool") or {}
        tool = tools_por_nombre.get(nombre_tool)
        if tool is None:
            resultado: dict[str, Any] = {
                "error": f"Herramienta desconocida o no enlazada: {nombre_tool!r}",
            }
            return {"resultado_tool": resultado, "fuentes": []}
        try:
            salida_tool = tool.invoke(args)
        except Exception as exc:  # noqa: BLE001 — aislar fallos de tool en respuesta trazable
            logger.exception("Fallo al ejecutar la tool %s", nombre_tool)
            return {
                "resultado_tool": {"error": str(exc)},
                "fuentes": [],
                "pensamientos": [
                    {
                        "tipo": "ejecucion_tool",
                        "herramienta": nombre_tool,
                        "razon_breve": "La tool lanzo una excepcion al ejecutarse.",
                    }
                ],
            }
        if not isinstance(salida_tool, dict):
            salida_tool = {"resultado": salida_tool}
        fuentes: list[dict[str, Any]] = []
        if nombre_tool == "rag_denso":
            raw = salida_tool.get("fuentes")
            if isinstance(raw, list):
                fuentes = [f for f in raw if isinstance(f, dict)]
        return {
            "resultado_tool": salida_tool,
            "fuentes": fuentes,
            "pensamientos": [
                {
                    "tipo": "ejecucion_tool",
                    "herramienta": nombre_tool,
                    "razon_breve": "Tool ejecutada; resultado disponible para el compositor.",
                }
            ],
        }

    def nodo_componer_respuesta(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        _ = config
        usuario = state.get("usuario") or {}
        nombre = str(usuario.get("nombre") or "").strip()
        usar_saludo = bool(
            state.get("primer_turno")
            and state.get("historial_previo_vacio")
            and nombre
        )
        bloques_sistema: list[str] = [texto_institucional]
        if usar_saludo:
            saludo = meta_prompt.saludo_template.replace("{nombre}", nombre)
            bloques_sistema.append(
                "Al inicio de la conversacion (sin historial previo en base de datos), "
                "comience la respuesta con el siguiente saludo institucional exacto "
                f"(puede continuar despues con el cuerpo de la respuesta):\n{saludo}"
            )
        elif state.get("primer_turno") and not state.get("historial_previo_vacio"):
            bloques_sistema.append(
                "Ya existe historial previo en esta sesion: no repita un saludo largo "
                "de bienvenida; mantenga continuidad con tono institucional sobrio."
            )
        bloques_sistema.append(
            "CONTEXTO DE HERRAMIENTA (resultado serializable de la ultima tool ejecutada):\n"
            + json.dumps(state.get("resultado_tool") or {}, ensure_ascii=False)
        )
        system_final = "\n\n".join(bloques_sistema)
        mensajes_compositor: list[BaseMessage] = [
            SystemMessage(content=system_final),
            HumanMessage(content=state["pregunta"]),
        ]
        salida = llm_compositor.invoke(mensajes_compositor)
        if not isinstance(salida, AIMessage):
            msg = f"El compositor debio devolver AIMessage; se obtuvo {type(salida)!r}."
            raise TypeError(msg)
        texto = salida.content
        if not isinstance(texto, str):
            texto = str(texto)
        return {"respuesta_final": texto}

    def nodo_persistir_turno(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        memoria = _obtener_memoria_desde_config(config)
        memoria.agregar_humano(state["pregunta"])
        meta_respuesta: dict[str, Any] = {
            "tool": state.get("tool_decidida"),
            "fuentes": state.get("fuentes") or [],
        }
        memoria.agregar_ai(state.get("respuesta_final") or "", metadata=meta_respuesta)
        return {}

    grafo = StateGraph(EstadoAgente)
    grafo.add_node("cargar_memoria", nodo_cargar_memoria)
    grafo.add_node("decidir_tool", nodo_decidir_tool)
    grafo.add_node("ejecutar_tool", nodo_ejecutar_tool)
    grafo.add_node("componer_respuesta", nodo_componer_respuesta)
    grafo.add_node("persistir_turno", nodo_persistir_turno)
    grafo.add_edge(START, "cargar_memoria")
    grafo.add_edge("cargar_memoria", "decidir_tool")
    grafo.add_edge("decidir_tool", "ejecutar_tool")
    grafo.add_edge("ejecutar_tool", "componer_respuesta")
    grafo.add_edge("componer_respuesta", "persistir_turno")
    grafo.add_edge("persistir_turno", END)
    return grafo.compile()
