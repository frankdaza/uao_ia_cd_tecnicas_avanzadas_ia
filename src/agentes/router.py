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
from src.agentes.prompt_institucional import PROMPT_SISTEMA_DEFECTO
from src.agentes.runtime_agente import RuntimeAgenteBundle
from src.api.configuracion import obtener_configuracion

logger = logging.getLogger(__name__)

CLAVE_MEMORIA_EN_CONFIG: str = "memoria"

_NOMBRES_TOOLS_OBLIGATORIAS: frozenset[str] = frozenset(
    {"faq_estructurada", "rag_denso", "listar_estructurado"}
)


def _texto_mensaje(mensaje: BaseMessage) -> str:
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    return str(contenido)


def _historial_a_texto_router(mensajes: list[BaseMessage], *, max_bloques: int | None = None) -> str:
    """Resume el historial en texto plano para el mensaje humano del router o el compositor."""
    if not mensajes:
        return "(sin mensajes previos en esta sesion)"
    ventana = mensajes if max_bloques is None else mensajes[-max_bloques:]
    lineas: list[str] = []
    for m in ventana:
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


def _construir_texto_sistema_router(meta: MetaPromptConfig) -> str:
    """
    Arma el system prompt del router: ``system_prompt`` mas bloques derivados del JSON
    (``reglas_decision`` y definicion pedagogica de ``herramientas``) para que ediciones
    desde el panel admin surtan efecto sin depender solo del texto base.
    """
    partes: list[str] = [meta.system_prompt.rstrip()]
    lineas_reglas = [r.strip() for r in meta.reglas_decision if isinstance(r, str) and r.strip()]
    if lineas_reglas:
        bloque_reglas = "\n".join(f"- {linea}" for linea in lineas_reglas)
        partes.append(
            "Reglas de decision (priorizar segun el enunciado y el contexto de la consulta):\n" + bloque_reglas
        )
    bloques_h: list[str] = []
    for h in meta.herramientas:
        sub = (
            f"### Herramienta `{h.name}`\n"
            f"Descripcion: {h.description.strip()}\n"
            f"Cuando usar: {h.when_to_use.strip()}"
        )
        if h.ejemplos:
            sub += "\nEjemplos de consultas:\n" + "\n".join(f"- {ej}" for ej in h.ejemplos if str(ej).strip())
        bloques_h.append(sub)
    if bloques_h:
        partes.append(
            "Referencia de herramientas disponibles (debe alinearse con las tool-calls del proveedor):\n\n"
            + "\n\n".join(bloques_h)
        )
    return "\n\n---\n\n".join(partes)


def _descripcion_tool_desde_meta(meta: MetaPromptConfig, nombre_tool: str) -> str | None:
    for h in meta.herramientas:
        if h.name == nombre_tool:
            bloques = [h.description.strip(), f"Criterio de uso: {h.when_to_use.strip()}"]
            ejemplos_txt = [str(e).strip() for e in h.ejemplos if str(e).strip()]
            if ejemplos_txt:
                bloques.append("Ejemplos de consultas:\n" + "\n".join(f"- {ej}" for ej in ejemplos_txt))
            return "\n\n".join(bloques)
    return None


def _tools_con_descripciones_de_meta(
    tools: Sequence[StructuredTool],
    meta: MetaPromptConfig,
) -> list[StructuredTool]:
    """Clona tools con ``description`` alineada al meta-prompt (admin / JSON) por nombre."""
    salida: list[StructuredTool] = []
    for t in tools:
        desc = _descripcion_tool_desde_meta(meta, t.name)
        if desc is not None:
            salida.append(t.model_copy(update={"description": desc}))
        else:
            salida.append(t)
    return salida


def crear_grafo_agente(
    *,
    llm_router: Any,
    llm_compositor: BaseChatModel,
    meta_prompt: MetaPromptConfig,
    herramientas: Sequence[StructuredTool] | None = None,
    prompt_sistema_institucional: str | None = None,
    etiqueta_modelo_compositor: str | None = None,
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
        Configuracion validada del JSON del router; ademas de ``system_prompt`` se inyectan
        ``reglas_decision`` y el detalle de ``herramientas`` en el mensaje de sistema del router,
        y las descripciones expuestas al proveedor en ``bind_tools`` se derivan del mismo objeto.
    herramientas:
        Tools enlazadas al router; por defecto ``faq_estructurada`` + ``rag_denso`` + ``listar_estructurado``.
    prompt_sistema_institucional:
        Texto base Lili; por defecto :data:`src.agentes.prompt_institucional.PROMPT_SISTEMA_DEFECTO`.
    etiqueta_modelo_compositor:
        Etiqueta legible del modelo del compositor (p. ej. para eventos SSE); por defecto ``agente``.

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
        from src.agentes.herramientas.listar_estructurado_tool import crear_listar_estructurado_tool
        from src.agentes.herramientas.rag_tool import crear_rag_tool

        tools = [crear_faq_tool(), crear_rag_tool(), crear_listar_estructurado_tool()]
    nombres = {t.name for t in tools}
    if not _NOMBRES_TOOLS_OBLIGATORIAS.issubset(nombres):
        msg = (
            "``herramientas`` debe incluir al menos las tools "
            f"{sorted(_NOMBRES_TOOLS_OBLIGATORIAS)} (recibido: {sorted(nombres)})."
        )
        raise ValueError(msg)
    tools_por_nombre: dict[str, StructuredTool] = {t.name: t for t in tools}
    texto_institucional = (prompt_sistema_institucional or PROMPT_SISTEMA_DEFECTO).rstrip()
    etiqueta_mc = (etiqueta_modelo_compositor or "agente").strip() or "agente"
    cfg_rag = obtener_configuracion()
    bundle_defecto = RuntimeAgenteBundle(
        llm_router=llm_router,
        llm_compositor=llm_compositor,
        meta_prompt=meta_prompt,
        prompt_institucional=texto_institucional,
        etiqueta_modelo_compositor=etiqueta_mc,
        rag_top_k=int(cfg_rag.rag_top_k),
        rag_score_minimo=float(cfg_rag.rag_score_minimo),
        historial_turnos_max=int(cfg_rag.historial_turnos_max),
    )

    def _bundle_desde_config(config: RunnableConfig) -> RuntimeAgenteBundle:
        configurable = config.get("configurable") or {}
        rt = configurable.get("runtime_agente")
        if isinstance(rt, RuntimeAgenteBundle):
            return rt
        return bundle_defecto

    def nodo_cargar_memoria(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        memoria = _obtener_memoria_desde_config(config)
        bundle_rt = _bundle_desde_config(config)
        mensajes = memoria.cargar_ventana(turnos_max=bundle_rt.historial_turnos_max)
        historial_previo_vacio = len(mensajes) == 0
        return {
            "mensajes_historial": mensajes,
            "historial_previo_vacio": historial_previo_vacio,
        }

    def nodo_inferir_intencion(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        _ = config
        from src.rag.intencion import inferir_intencion

        intencion = inferir_intencion(str(state.get("pregunta") or ""))
        return {"intencion": intencion}

    def nodo_decidir_tool(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        bundle = _bundle_desde_config(config)
        meta = bundle.meta_prompt
        pregunta = str(state.get("pregunta") or "")
        intencion = str(state.get("intencion") or "factual")

        if intencion in ("listado", "conteo"):
            from src.rag.filtros_listado_heuristica import extraer_filtros_listado_desde_pregunta

            filtros_h = extraer_filtros_listado_desde_pregunta(pregunta)
            if filtros_h:
                args_tool: dict[str, Any] = {"limite": 50, **filtros_h}
                mensaje_ai = AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "listar_estructurado",
                            "args": args_tool,
                            "id": "call_heuristica_intencion",
                            "type": "tool_call",
                        }
                    ],
                )
                pensamiento = {
                    "tipo": "decision_router",
                    "herramienta": "listar_estructurado",
                    "razon_breve": (
                        "Intencion de listado o conteo con filtros inferidos localmente "
                        "(sin invocar al LLM del router)."
                    ),
                    "argumentos_resumidos": _argumentos_serializables(args_tool),
                }
                return {
                    "mensaje_router": mensaje_ai,
                    "tool_decidida": "listar_estructurado",
                    "argumentos_tool": args_tool,
                    "pensamientos": [pensamiento],
                }

        historial_txt = _historial_a_texto_router(state.get("mensajes_historial") or [], max_bloques=None)
        contenido_humano = f"{historial_txt}\n\n---\n\nConsulta actual del usuario:\n{state['pregunta']}"
        texto_sistema = _construir_texto_sistema_router(meta)
        mensajes_router: list[BaseMessage] = [
            SystemMessage(content=texto_sistema),
            HumanMessage(content=contenido_humano),
        ]
        tools_router = _tools_con_descripciones_de_meta(tools, meta)
        enlazado = bundle.llm_router.bind_tools(tools_router)
        mensaje_ai: AIMessage = enlazado.invoke(mensajes_router)
        tool_decidida: str | None = None
        argumentos_tool: dict[str, Any] = {}
        if mensaje_ai.tool_calls:
            principal = mensaje_ai.tool_calls[0]
            tool_decidida = principal["name"]
            argumentos_tool = dict(principal.get("args") or {})
            razon_breve = "Seleccion vía tool binding del LLM del router segun meta-prompt."
        else:
            logger.warning(
                "El router no devolvio tool_calls; se usa rag_denso como respaldo deterministico."
            )
            tool_decidida = "rag_denso"
            argumentos_tool = {"consulta": state["pregunta"]}
            razon_breve = "Router sin tool_calls; fallback a rag_denso."
        if tool_decidida == "rag_denso":
            from src.rag.intencion import inferir_filtros_tipo_pagina_para_rag

            sugeridos = inferir_filtros_tipo_pagina_para_rag(pregunta)
            if sugeridos and not argumentos_tool.get("filtros_tipo_pagina"):
                argumentos_tool = {**argumentos_tool, "filtros_tipo_pagina": sugeridos}
        pensamiento = {
            "tipo": "decision_router",
            "herramienta": tool_decidida,
            "razon_breve": razon_breve,
            "argumentos_resumidos": _argumentos_serializables(argumentos_tool),
        }
        return {
            "mensaje_router": mensaje_ai,
            "tool_decidida": tool_decidida,
            "argumentos_tool": argumentos_tool,
            "pensamientos": [pensamiento],
        }

    def nodo_ejecutar_tool(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        bundle = _bundle_desde_config(config)
        nombre_tool = state.get("tool_decidida") or ""
        args = state.get("argumentos_tool") or {}
        args_invocacion = dict(args)
        if nombre_tool == "faq_estructurada":
            pregunta_txt = str(state.get("pregunta") or "").strip()
            cq = str(args_invocacion.get("consulta") or "").strip()
            if not cq or (
                pregunta_txt
                and len(cq) < max(24, int(len(pregunta_txt) * 0.5))
            ):
                args_invocacion["consulta"] = pregunta_txt or cq
        tool = tools_por_nombre.get(nombre_tool)
        if tool is None:
            resultado: dict[str, Any] = {
                "error": f"Herramienta desconocida o no enlazada: {nombre_tool!r}",
            }
            return {"resultado_tool": resultado, "fuentes": []}
        try:
            if nombre_tool == "rag_denso":
                from src.agentes.herramientas.rag_tool import ejecutar_rag_denso_sync

                cfg = obtener_configuracion()
                mismo_que_env = bundle.rag_top_k == int(cfg.rag_top_k) and abs(
                    bundle.rag_score_minimo - float(cfg.rag_score_minimo)
                ) <= 1e-9
                if mismo_que_env:
                    salida_tool = tool.invoke(args_invocacion)
                else:
                    consulta_txt = str(args_invocacion.get("consulta") or "")
                    ft = args_invocacion.get("filtros_tipo_pagina")
                    salida_tool = ejecutar_rag_denso_sync(
                        configuracion=cfg,
                        consulta=consulta_txt,
                        top_k=bundle.rag_top_k,
                        score_minimo=bundle.rag_score_minimo,
                        filtros_tipo_pagina=ft if isinstance(ft, list) else None,
                    )
            else:
                salida_tool = tool.invoke(args_invocacion)
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
        nombre_efectivo = str(nombre_tool or "")
        if nombre_efectivo == "listar_estructurado" and int(salida_tool.get("conteo") or 0) == 0:
            from src.agentes.herramientas.rag_tool import ejecutar_rag_denso_sync
            from src.rag.intencion import inferir_filtros_tipo_pagina_para_rag

            cfg = obtener_configuracion()
            fj = inferir_filtros_tipo_pagina_para_rag(str(state.get("pregunta") or ""))
            salida_tool = ejecutar_rag_denso_sync(
                configuracion=cfg,
                consulta=str(state.get("pregunta") or "").strip(),
                top_k=bundle.rag_top_k,
                score_minimo=bundle.rag_score_minimo,
                filtros_tipo_pagina=fj,
            )
            nombre_efectivo = "rag_denso"
        fuentes: list[dict[str, Any]] = []
        if nombre_efectivo == "rag_denso":
            raw = salida_tool.get("fuentes")
            if isinstance(raw, list):
                fuentes = [f for f in raw if isinstance(f, dict)]
        razon_ejec = "Tool ejecutada; resultado disponible para el compositor."
        if str(nombre_tool or "") == "listar_estructurado" and nombre_efectivo == "rag_denso":
            razon_ejec = (
                "listar_estructurado sin coincidencias; respaldo a rag_denso con la consulta original."
            )
        pensamiento_ejec: dict[str, Any] = {
            "tipo": "ejecucion_tool",
            "herramienta": nombre_efectivo,
            "razon_breve": razon_ejec,
        }
        if nombre_efectivo == "faq_estructurada" and isinstance(salida_tool, dict):
            um_faq = float(obtener_configuracion().faq_umbral_match)
            cq_ej = str(args_invocacion.get("consulta") or "")
            pensamiento_ejec["faq_umbral_match"] = um_faq
            pensamiento_ejec["faq_match_encontrado"] = bool(salida_tool.get("encontrado"))
            pensamiento_ejec["faq_consulta_ejecutada"] = (
                cq_ej if len(cq_ej) <= 400 else cq_ej[:400] + "…"
            )
        salida_estado: dict[str, Any] = {
            "resultado_tool": salida_tool,
            "fuentes": fuentes,
            "pensamientos": [pensamiento_ejec],
        }
        if nombre_efectivo != nombre_tool:
            salida_estado["tool_decidida"] = nombre_efectivo
        return salida_estado

    def nodo_componer_respuesta(state: EstadoAgente, config: RunnableConfig) -> dict[str, Any]:
        bundle = _bundle_desde_config(config)
        meta = bundle.meta_prompt
        usuario = state.get("usuario") or {}
        nombre = str(usuario.get("nombre") or "").strip()
        usar_saludo = bool(
            state.get("primer_turno")
            and state.get("historial_previo_vacio")
            and nombre
        )
        bloques_sistema: list[str] = [bundle.prompt_institucional]
        if nombre:
            bloques_sistema.append(
                "Datos del usuario autenticado en esta sesion (usar para trato personal; "
                "no confundir con fragmentos del corpus institucional ni con fuentes bibliograficas del RAG):\n"
                f"- Nombre registrado al iniciar sesion: {nombre}"
            )
        if usar_saludo:
            saludo = meta.saludo_template.replace("{nombre}", nombre)
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
        previos = state.get("mensajes_historial") or []
        if previos:
            historial_txt = _historial_a_texto_router(previos, max_bloques=None)
            bloques_sistema.append(
                "Historial reciente de la conversacion (turnos ya completados en esta sesion). "
                "No inventar hechos que no consten aqui ni en el contexto de herramienta debajo:\n"
                + historial_txt
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
        texto = ""
        for trozo in bundle.llm_compositor.stream(mensajes_compositor):
            if isinstance(trozo, AIMessage):
                c = trozo.content
            else:
                c = getattr(trozo, "content", trozo)
            if isinstance(c, str) and c:
                texto += c
            elif isinstance(c, list):
                for bloque in c:
                    if isinstance(bloque, dict) and bloque.get("type") == "text":
                        t = bloque.get("text")
                        if isinstance(t, str):
                            texto += t
        if not texto.strip():
            salida = bundle.llm_compositor.invoke(mensajes_compositor)
            if not isinstance(salida, AIMessage):
                msg = f"El compositor debio devolver AIMessage; se obtuvo {type(salida)!r}."
                raise TypeError(msg)
            cfinal = salida.content
            texto = cfinal if isinstance(cfinal, str) else str(cfinal)
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
    grafo.add_node("inferir_intencion", nodo_inferir_intencion)
    grafo.add_node("decidir_tool", nodo_decidir_tool)
    grafo.add_node("ejecutar_tool", nodo_ejecutar_tool)
    grafo.add_node("componer_respuesta", nodo_componer_respuesta)
    grafo.add_node("persistir_turno", nodo_persistir_turno)
    grafo.add_edge(START, "cargar_memoria")
    grafo.add_edge("cargar_memoria", "inferir_intencion")
    grafo.add_edge("inferir_intencion", "decidir_tool")
    grafo.add_edge("decidir_tool", "ejecutar_tool")
    grafo.add_edge("ejecutar_tool", "componer_respuesta")
    grafo.add_edge("componer_respuesta", "persistir_turno")
    grafo.add_edge("persistir_turno", END)
    return grafo.compile()
