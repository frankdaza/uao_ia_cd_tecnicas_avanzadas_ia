"""
Grafo LangGraph (StateGraph) del agente conversacional M2.

Define el flujo lineal: cargar memoria -> inferir intencion -> decidir tool (router LLM o
heuristica) -> ejecutar tool -> componer respuesta institucional -> persistir turno. Las
funciones privadas preparan prompts, serializan argumentos para trazabilidad y unifican la
invocacion de RAG con parametros del bundle de runtime.
"""

from __future__ import annotations

import asyncio
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
from src.agentes.reglas import (
    coercionar_historial_dias_max,
    coercionar_historial_turnos_max,
    coercionar_top_k_final,
    coercionar_top_k_inicial,
)
from src.agentes.runtime_agente import RuntimeAgenteBundle
from src.api.configuracion import obtener_configuracion

logger = logging.getLogger(__name__)


def _argumentos_invocacion_rag_denso(
    args_tool: dict[str, Any],
    bundle: RuntimeAgenteBundle,
) -> dict[str, Any]:
    """
    Construye el diccionario de argumentos que recibe la tool ``rag_denso`` al invocarse.

    Pasos:
    1. Lee ``consulta`` y ``filtros_tipo_pagina`` de lo que devolvio el router (si aplica).
    2. Normaliza ``filtros_tipo_pagina`` a lista o ``None`` (evita tipos inesperados).
    3. Copia desde ``bundle`` los hiperparametros de recuperacion (top_k, score minimo, MMR,
       reranker, etc.) para que **toda** la ejecucion RAG use la misma politica configurada
       en runtime y no dependa de que el modelo las invente en el tool-call.
    """
    ft = args_tool.get("filtros_tipo_pagina")
    return {
        "consulta": str(args_tool.get("consulta") or ""),
        "filtros_tipo_pagina": ft if isinstance(ft, list) else None,
        "top_k": bundle.rag_top_k,
        "score_minimo": bundle.rag_score_minimo,
        "top_k_inicial": bundle.rag_top_k_inicial,
        "mmr_habilitado": bundle.rag_mmr_habilitado,
        "mmr_lambda": bundle.rag_mmr_lambda,
        "reranker_habilitado": bundle.rag_reranker_habilitado,
        "reranker_modelo": bundle.rag_reranker_modelo,
        "reranker_top_n_entrada": bundle.rag_reranker_top_n_entrada,
        "reranker_batch_size": bundle.rag_reranker_batch_size,
    }


CLAVE_MEMORIA_EN_CONFIG: str = "memoria"

_NOMBRES_TOOLS_OBLIGATORIAS: frozenset[str] = frozenset(
    {"faq_estructurada", "rag_denso", "listar_estructurado"}
)


def _texto_mensaje(mensaje: BaseMessage) -> str:
    """
    Obtiene el texto legible del ``content`` de un mensaje LangChain.

    Pasos:
    1. Lee ``mensaje.content``.
    2. Si ya es ``str``, lo devuelve tal cual.
    3. Si no (bloques multimodales u otros tipos), lo convierte con ``str(...)`` para poder
       resumirlo en el historial del router o del compositor.
    """
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    return str(contenido)


def _historial_a_texto_router(
    mensajes: list[BaseMessage], *, max_bloques: int | None = None
) -> str:
    """
    Convierte una lista de mensajes en un bloque de texto etiquetado (usuario / asistente).

    Pasos:
    1. Si no hay mensajes, devuelve un marcador fijo de sesion vacia.
    2. Opcionalmente recorta a los ultimos ``max_bloques`` mensajes (ventana); si es ``None``,
       usa el historial completo recibido.
    3. Recorre cada mensaje: ``HumanMessage`` -> prefijo ``usuario:``, ``AIMessage`` ->
       prefijo ``asistente:``; ignora otros roles para este resumen.
    4. Trunca cada linea a ~1800 caracteres para no inflar prompts.
    5. Une con saltos de linea; si no quedo ninguna linea util, devuelve el marcador de vacio.
    """
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
    """
    Extrae de ``RunnableConfig`` la instancia de memoria de usuario requerida por el grafo.

    Pasos:
    1. Lee ``config["configurable"]`` (dict) o dict vacio si falta.
    2. Busca la clave :data:`CLAVE_MEMORIA_EN_CONFIG` (``"memoria"``).
    3. Si no esta definida, lanza ``ValueError`` con mensaje que indica como invocar el grafo.
    4. Devuelve el objeto memoria (debe exponer ``cargar_ventana``, ``agregar_humano``,
       ``agregar_ai`` segun el contrato del proyecto).
    """
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
    """
    Copia argumentos de tool para guardarlos en ``pensamientos`` sin saturar logs ni SSE.

    Pasos:
    1. Itera clave/valor del dict de argumentos.
    2. Para cada valor ``str`` mayor a 400 caracteres, trunca y agrega elipsis Unicode.
    3. Para valores no string, los copia tal cual (listas, numeros, etc.).
    """
    salida: dict[str, Any] = {}
    for clave, valor in argumentos.items():
        if isinstance(valor, str):
            salida[clave] = valor if len(valor) <= 400 else valor[:400] + "…"
        else:
            salida[clave] = valor
    return salida


def _construir_texto_sistema_router(meta: MetaPromptConfig) -> str:
    """
    Arma el mensaje de sistema que ve el LLM del router antes de decidir tool-calls.

    Pasos:
    1. Parte del ``system_prompt`` base del meta-prompt (JSON admin), sin espacios finales.
    2. Si hay ``reglas_decision`` no vacias, agrega un bloque con viñetas priorizables.
    3. Por cada entrada en ``meta.herramientas``, genera un bloque Markdown con nombre,
       descripcion, criterio ``when_to_use`` y ejemplos opcionales.
    4. Concatena secciones separadas por ``\\n\\n---\\n\\n`` para delimitar contexto.
    """
    partes: list[str] = [meta.system_prompt.rstrip()]
    lineas_reglas = [
        r.strip() for r in meta.reglas_decision if isinstance(r, str) and r.strip()
    ]
    if lineas_reglas:
        bloque_reglas = "\n".join(f"- {linea}" for linea in lineas_reglas)
        partes.append(
            "Reglas de decision (priorizar segun el enunciado y el contexto de la consulta):\n"
            + bloque_reglas
        )
    bloques_h: list[str] = []
    for h in meta.herramientas:
        sub = (
            f"### Herramienta `{h.name}`\n"
            f"Descripcion: {h.description.strip()}\n"
            f"Cuando usar: {h.when_to_use.strip()}"
        )
        if h.ejemplos:
            sub += "\nEjemplos de consultas:\n" + "\n".join(
                f"- {ej}" for ej in h.ejemplos if str(ej).strip()
            )
        bloques_h.append(sub)
    if bloques_h:
        partes.append(
            "Referencia de herramientas disponibles (debe alinearse con las tool-calls del proveedor):\n\n"
            + "\n\n".join(bloques_h)
        )
    return "\n\n---\n\n".join(partes)


def _descripcion_tool_desde_meta(
    meta: MetaPromptConfig, nombre_tool: str
) -> str | None:
    """
    Busca en el meta-prompt la definicion pedagogica de una tool por su ``name``.

    Pasos:
    1. Recorre ``meta.herramientas`` buscando coincidencia de ``h.name`` con ``nombre_tool``.
    2. Si encuentra, arma texto con descripcion, criterio de uso y ejemplos (si existen).
    3. Si no hay coincidencia, devuelve ``None`` (el caller deja la descripcion original de la tool).
    """
    for h in meta.herramientas:
        if h.name == nombre_tool:
            bloques = [
                h.description.strip(),
                f"Criterio de uso: {h.when_to_use.strip()}",
            ]
            ejemplos_txt = [str(e).strip() for e in h.ejemplos if str(e).strip()]
            if ejemplos_txt:
                bloques.append(
                    "Ejemplos de consultas:\n"
                    + "\n".join(f"- {ej}" for ej in ejemplos_txt)
                )
            return "\n\n".join(bloques)
    return None


def _tools_con_descripciones_de_meta(
    tools: Sequence[StructuredTool],
    meta: MetaPromptConfig,
) -> list[StructuredTool]:
    """
    Devuelve una lista de tools lista para ``bind_tools``, con textos alineados al JSON.

    Pasos:
    1. Por cada ``StructuredTool`` de entrada, intenta obtener texto con
       :func:`_descripcion_tool_desde_meta`.
    2. Si hay texto, clona la tool con ``model_copy(update={"description": ...})``.
    3. Si no hay entrada en meta para ese nombre, deja la tool sin modificar.
    """
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

    Flujo del grafo (orden de nodos)
    --------------------------------
    1. ``cargar_memoria``: lee ventana de historial desde Postgres vía memoria inyectada.
    2. ``inferir_intencion``: clasifica la pregunta (p. ej. factual vs listado) con heuristica local.
    3. ``decidir_tool``: o bien fuerza ``listar_estructurado`` con filtros inferidos, o invoca el
       LLM router con tools enlazadas; si no hay tool_calls, hace fallback a ``rag_denso``.
    4. ``ejecutar_tool``: invoca la tool elegida; unifica args RAG; puede rebalancear a RAG si
       listado devuelve conteo cero.
    5. ``componer_respuesta``: arma system prompt institucional + JSON del resultado de tool y
       hace streaming (o invoke) con el compositor.
    6. ``persistir_turno``: guarda turno humano y respuesta del asistente con metadata (tool,
       fuentes).

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
        Grafo compilado. Invocacion tipica (API async; los nodos son ``async``)::

            await grafo.ainvoke(
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
        from src.agentes.herramientas.listar_estructurado_tool import (
            crear_listar_estructurado_tool,
        )
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
    texto_institucional = (
        prompt_sistema_institucional or PROMPT_SISTEMA_DEFECTO
    ).rstrip()
    etiqueta_mc = (etiqueta_modelo_compositor or "agente").strip() or "agente"
    cfg_rag = obtener_configuracion()
    bundle_defecto = RuntimeAgenteBundle(
        llm_router=llm_router,
        llm_compositor=llm_compositor,
        meta_prompt=meta_prompt,
        prompt_institucional=texto_institucional,
        etiqueta_modelo_compositor=etiqueta_mc,
        rag_top_k=coercionar_top_k_final(int(cfg_rag.rag_top_k)),
        rag_score_minimo=float(cfg_rag.rag_score_minimo),
        historial_turnos_max=coercionar_historial_turnos_max(
            int(cfg_rag.historial_turnos_max)
        ),
        historial_dias_max=coercionar_historial_dias_max(
            int(cfg_rag.historial_dias_max)
        ),
        rag_top_k_inicial=coercionar_top_k_inicial(int(cfg_rag.rag_top_k_inicial)),
        rag_mmr_habilitado=bool(cfg_rag.rag_mmr_habilitado),
        rag_mmr_lambda=float(cfg_rag.rag_mmr_lambda),
        rag_reranker_habilitado=bool(cfg_rag.rag_reranker_habilitado),
        rag_reranker_modelo=str(cfg_rag.rag_reranker_modelo).strip(),
        rag_reranker_top_n_entrada=int(cfg_rag.rag_reranker_top_n_entrada),
        rag_reranker_batch_size=int(cfg_rag.rag_reranker_batch_size),
    )

    def _bundle_desde_config(config: RunnableConfig) -> RuntimeAgenteBundle:
        """
        Resuelve el ``RuntimeAgenteBundle`` activo para esta invocacion del grafo.

        Pasos:
        1. Lee ``config["configurable"].get("runtime_agente")``.
        2. Si es una instancia de :class:`RuntimeAgenteBundle`, la devuelve (permite tests o
           override por peticion).
        3. Si no, devuelve ``bundle_defecto`` construido al compilar el grafo (LLMs, meta-prompt,
           limites RAG desde configuracion).
        """
        configurable = config.get("configurable") or {}
        rt = configurable.get("runtime_agente")
        if isinstance(rt, RuntimeAgenteBundle):
            return rt
        return bundle_defecto

    async def nodo_cargar_memoria(
        state: EstadoAgente, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Nodo inicial: hidrata el estado con el historial persistido del usuario.

        Pasos:
        1. Obtiene memoria desde ``config`` (:func:`_obtener_memoria_desde_config`).
        2. Resuelve ``bundle`` para conocer ``historial_turnos_max``.
        3. Llama ``memoria.cargar_ventana(turnos_max=...)`` y guarda la lista en
           ``mensajes_historial``.
        4. Calcula ``historial_previo_vacio`` (``True`` si no habia mensajes antes de este turno).
        """
        memoria = _obtener_memoria_desde_config(config)
        bundle_rt = _bundle_desde_config(config)

        def _cargar() -> tuple[list[BaseMessage], bool]:
            mensajes_loc = memoria.cargar_ventana(
                turnos_max=bundle_rt.historial_turnos_max
            )
            return mensajes_loc, len(mensajes_loc) == 0

        mensajes, historial_previo_vacio = await asyncio.to_thread(_cargar)
        return {
            "mensajes_historial": mensajes,
            "historial_previo_vacio": historial_previo_vacio,
        }

    async def nodo_inferir_intencion(
        state: EstadoAgente, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Clasifica la intencion de la pregunta actual sin llamar al LLM del router.

        Pasos:
        1. Ignora ``config`` (firma uniforme de nodos LangGraph).
        2. Llama :func:`src.rag.runtime.intencion.inferir_intencion` con el texto de ``state["pregunta"]``.
        3. Escribe el label resultante en ``intencion`` del estado (p. ej. para ramificar decision
           de tool en el siguiente nodo).
        """
        _ = config
        from src.rag.runtime.intencion import inferir_intencion

        intencion = inferir_intencion(str(state.get("pregunta") or ""))
        return {"intencion": intencion}

    async def nodo_decidir_tool(
        state: EstadoAgente, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Elige que tool ejecutar y con que argumentos, usando heuristica o LLM router.

        Pasos:
        1. Resuelve ``bundle`` y ``meta_prompt``; lee ``pregunta`` e ``intencion`` del estado.
        2. **Atajo listado/conteo**: si ``intencion`` es ``listado`` o ``conteo``, intenta extraer
           filtros con heuristica; si hay filtros, fabrica un ``AIMessage`` sintetico con un
           ``tool_call`` a ``listar_estructurado`` y retorna (sin LLM router).
        3. **Camino LLM**: construye texto de historial + consulta actual (:func:`_historial_a_texto_router`),
           system con :func:`_construir_texto_sistema_router`, y mensajes ``SystemMessage`` +
           ``HumanMessage``.
        4. Enlaza tools con descripciones del meta-prompt (:func:`_tools_con_descripciones_de_meta`),
           ``bind_tools`` e ``invoke`` sobre el router.
        5. Si el router devuelve ``tool_calls``, toma el primero (nombre y args); si no, registra
           warning y hace **fallback** a ``rag_denso`` con ``consulta`` = pregunta.
        6. Para ``rag_denso``, si faltan ``filtros_tipo_pagina``, puede sugerirlos con
           :func:`src.rag.runtime.intencion.inferir_filtros_tipo_pagina_para_rag`.
        7. Arma un dict ``pensamiento`` de tipo ``decision_router`` y devuelve ``mensaje_router``,
           ``tool_decidida``, ``argumentos_tool`` y ``pensamientos``.
        """
        bundle = _bundle_desde_config(config)
        meta = bundle.meta_prompt
        pregunta = str(state.get("pregunta") or "")
        intencion = str(state.get("intencion") or "factual")

        if intencion in ("listado", "conteo"):
            from src.rag.runtime.filtros_listado_heuristica import (
                extraer_filtros_listado_desde_pregunta,
            )

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

        historial_txt = _historial_a_texto_router(
            state.get("mensajes_historial") or [], max_bloques=None
        )
        contenido_humano = f"{historial_txt}\n\n---\n\nConsulta actual del usuario:\n{state['pregunta']}"
        texto_sistema = _construir_texto_sistema_router(meta)
        mensajes_router: list[BaseMessage] = [
            SystemMessage(content=texto_sistema),
            HumanMessage(content=contenido_humano),
        ]
        tools_router = _tools_con_descripciones_de_meta(tools, meta)
        enlazado = bundle.llm_router.bind_tools(tools_router)
        mensaje_ai: AIMessage
        if hasattr(enlazado, "ainvoke"):
            mensaje_ai = await enlazado.ainvoke(mensajes_router)
        else:
            mensaje_ai = await asyncio.to_thread(enlazado.invoke, mensajes_router)
        tool_decidida: str | None = None
        argumentos_tool: dict[str, Any] = {}
        if mensaje_ai.tool_calls:
            if len(mensaje_ai.tool_calls) > 1:
                logger.warning(
                    "El router devolvio %s tool_calls; solo se procesa la primera.",
                    len(mensaje_ai.tool_calls),
                )
            principal = mensaje_ai.tool_calls[0]
            tool_decidida = principal["name"]
            argumentos_tool = dict(principal.get("args") or {})
            razon_breve = (
                "Seleccion vía tool binding del LLM del router segun meta-prompt."
            )
        else:
            logger.warning(
                "El router no devolvio tool_calls; se usa rag_denso como respaldo deterministico."
            )
            tool_decidida = "rag_denso"
            argumentos_tool = {"consulta": state["pregunta"]}
            razon_breve = "Router sin tool_calls; fallback a rag_denso."
        if tool_decidida == "rag_denso":
            from src.rag.runtime.intencion import inferir_filtros_tipo_pagina_para_rag

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

    async def nodo_ejecutar_tool(
        state: EstadoAgente, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Ejecuta la tool seleccionada y normaliza salida, fuentes y trazabilidad.

        Pasos:
        1. Lee ``tool_decidida`` y ``argumentos_tool``; copia args en ``args_invocacion``.
        2. **FAQ**: si la consulta en args es vacia o demasiado corta frente a la pregunta del
           usuario, rellena ``consulta`` con el texto de la pregunta actual.
        3. Busca la ``StructuredTool`` por nombre; si no existe, devuelve dict de error y sin fuentes.
        4. **RAG**: si la tool es ``rag_denso``, invoca con :func:`_argumentos_invocacion_rag_denso`
           (parametros RAG siempre desde ``bundle``); en otro caso ``invoke`` directo con args.
        5. Ante excepcion, loguea, devuelve error serializable y un pensamiento ``ejecucion_tool``.
        6. Si la salida no es ``dict``, la envuelve en ``{"resultado": ...}``.
        7. **Rescate listado vacio**: si era ``listar_estructurado`` y ``conteo`` es 0, ejecuta
           ``rag_denso`` con la pregunta original y filtros inferidos; actualiza nombre efectivo
           y opcionalmente ``tool_decidida`` en el estado devuelto.
        8. Si la tool efectiva fue RAG, extrae la lista ``fuentes`` (solo dicts) para el front.
        9. Construye pensamiento de ejecucion (incluye metadatos FAQ si aplica) y retorna
           ``resultado_tool``, ``fuentes`` y ``pensamientos``.
        """
        bundle = _bundle_desde_config(config)
        nombre_tool = state.get("tool_decidida") or ""
        args = state.get("argumentos_tool") or {}
        args_invocacion = dict(args)
        if nombre_tool == "faq_estructurada":
            pregunta_txt = str(state.get("pregunta") or "").strip()
            cq = str(args_invocacion.get("consulta") or "").strip()
            if not cq or (
                pregunta_txt and len(cq) < max(24, int(len(pregunta_txt) * 0.5))
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
                args_rag = _argumentos_invocacion_rag_denso(args_invocacion, bundle)
                if hasattr(tool, "ainvoke"):
                    salida_tool = await tool.ainvoke(args_rag)
                else:
                    salida_tool = await asyncio.to_thread(tool.invoke, args_rag)
            elif hasattr(tool, "ainvoke"):
                salida_tool = await tool.ainvoke(args_invocacion)
            else:
                salida_tool = await asyncio.to_thread(tool.invoke, args_invocacion)
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
        if (
            nombre_efectivo == "listar_estructurado"
            and int(salida_tool.get("conteo") or 0) == 0
        ):
            from src.rag.runtime.intencion import inferir_filtros_tipo_pagina_para_rag

            fj = inferir_filtros_tipo_pagina_para_rag(str(state.get("pregunta") or ""))
            tool_rag = tools_por_nombre["rag_denso"]
            args_fb = _argumentos_invocacion_rag_denso(
                {
                    "consulta": str(state.get("pregunta") or "").strip(),
                    "filtros_tipo_pagina": fj,
                },
                bundle,
            )
            if hasattr(tool_rag, "ainvoke"):
                salida_tool = await tool_rag.ainvoke(args_fb)
            else:
                salida_tool = await asyncio.to_thread(tool_rag.invoke, args_fb)
            nombre_efectivo = "rag_denso"
        fuentes: list[dict[str, Any]] = []
        if nombre_efectivo == "rag_denso":
            raw = salida_tool.get("fuentes")
            if isinstance(raw, list):
                fuentes = [f for f in raw if isinstance(f, dict)]
        razon_ejec = "Tool ejecutada; resultado disponible para el compositor."
        if (
            str(nombre_tool or "") == "listar_estructurado"
            and nombre_efectivo == "rag_denso"
        ):
            razon_ejec = "listar_estructurado sin coincidencias; respaldo a rag_denso con la consulta original."
        pensamiento_ejec: dict[str, Any] = {
            "tipo": "ejecucion_tool",
            "herramienta": nombre_efectivo,
            "razon_breve": razon_ejec,
        }
        if nombre_efectivo == "faq_estructurada" and isinstance(salida_tool, dict):
            um_faq = float(obtener_configuracion().faq_umbral_match)
            cq_ej = str(args_invocacion.get("consulta") or "")
            pensamiento_ejec["faq_umbral_match"] = um_faq
            pensamiento_ejec["faq_match_encontrado"] = bool(
                salida_tool.get("encontrado")
            )
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

    async def nodo_componer_respuesta(
        state: EstadoAgente, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Genera la respuesta final al usuario con el LLM compositor (politica institucional Lili).

        Pasos:
        1. Resuelve ``bundle`` y datos de ``usuario`` (nombre) desde el estado.
        2. Decide si corresponde **saludo** obligatorio: primer turno, historial previo vacio y
           nombre presente; usa ``meta.saludo_template`` con placeholder ``{nombre}``.
        3. Si es primer turno pero ya habia historial, agrega instruccion de no repetir saludo largo.
        4. Si hay mensajes previos cargados, agrega bloque de historial reciente en texto plano.
        5. Serializa ``resultado_tool`` a JSON UTF-8 como ``CONTEXTO DE HERRAMIENTA`` en el system.
        6. Arma mensajes ``SystemMessage`` + ``HumanMessage`` con la pregunta actual y hace
           **stream** asincrono del compositor cuando esta disponible.
        7. Si el stream no produjo texto, hace ``ainvoke`` de respaldo y exige ``AIMessage``.
        8. Devuelve ``respuesta_final`` como string unico.
        """
        bundle = _bundle_desde_config(config)
        meta = bundle.meta_prompt
        usuario = state.get("usuario") or {}
        nombre = str(usuario.get("nombre") or "").strip()
        usar_saludo = bool(
            state.get("primer_turno") and state.get("historial_previo_vacio") and nombre
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
        llm_c = bundle.llm_compositor
        if hasattr(llm_c, "astream"):
            async for trozo in llm_c.astream(mensajes_compositor):
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
        else:
            for trozo in llm_c.stream(mensajes_compositor):
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
            if hasattr(llm_c, "ainvoke"):
                salida = await llm_c.ainvoke(mensajes_compositor)
            else:
                salida = await asyncio.to_thread(llm_c.invoke, mensajes_compositor)
            if not isinstance(salida, AIMessage):
                msg = f"El compositor debio devolver AIMessage; se obtuvo {type(salida)!r}."
                raise TypeError(msg)
            cfinal = salida.content
            texto = cfinal if isinstance(cfinal, str) else str(cfinal)
        return {"respuesta_final": texto}

    async def nodo_persistir_turno(
        state: EstadoAgente, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Persiste en memoria el turno humano y la respuesta del asistente con metadata.

        Pasos:
        1. Obtiene memoria desde ``config``.
        2. ``agregar_humano`` con el texto de ``state["pregunta"]``.
        3. Arma metadata con ``tool`` usada y lista ``fuentes`` (si hubo RAG).
        4. ``agregar_ai`` con ``respuesta_final`` y esa metadata para el historial LangChain.
        5. Devuelve dict vacio (no muta mas campos del estado del grafo).
        """
        memoria = _obtener_memoria_desde_config(config)

        def _persistir() -> None:
            memoria.agregar_humano(state["pregunta"])
            meta_respuesta: dict[str, Any] = {
                "tool": state.get("tool_decidida"),
                "fuentes": state.get("fuentes") or [],
            }
            memoria.agregar_ai(
                state.get("respuesta_final") or "", metadata=meta_respuesta
            )

        await asyncio.to_thread(_persistir)
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
