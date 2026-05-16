"""
Endpoint del agente conversacional (Modulo 2): streaming SSE con eventos extendidos.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator, Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from sse_starlette.sse import EventSourceResponse

from psycopg_pool import ConnectionPool

from src.agentes.memoria.historial import (
    MemoriaConexionError,
    MemoriaUsuario,
    normalizar_session_id_postgres_langchain,
)
from src.agentes.reglas import construir_limites_historial
from src.agentes.runtime_agente import RuntimeAgenteBundle
from src.api.dependencias import (
    obtener_bundle_runtime_agente,
    obtener_grafo_agente,
    obtener_pool_memoria_psycopg,
    obtener_usuario_actual,
)
from src.api.esquemas import (
    EventoError,
    EventoFinal,
    EventoFuentes,
    EventoHerramienta,
    EventoPensamiento,
    EventoToken,
    PeticionAgente,
)
from src.persistencia.modelos import Usuario
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agente"])

_KEEPALIVE_SEG = 15


def _session_id_autorizado(peticion: PeticionAgente, usuario: Usuario) -> None:
    """Exige que el cuerpo coincida con la sesion resuelta por cookie/cabecera."""
    esperado = sesion_id_memoria_langchain(usuario.id)
    enviado = peticion.session_id.strip()
    if enviado == esperado:
        return
    try:
        uuid_txt = normalizar_session_id_postgres_langchain(enviado)
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail="El session_id no coincide con la sesion autenticada.",
        ) from exc
    if uuid_txt != str(usuario.id):
        raise HTTPException(
            status_code=403,
            detail="El session_id no coincide con la sesion autenticada.",
        )


def _meta_nodo(ev: Mapping[str, Any]) -> str | None:
    meta = ev.get("metadata")
    if not isinstance(meta, dict):
        return None
    nodo = meta.get("langgraph_node")
    return str(nodo) if nodo is not None else None


def _extraer_texto_delta_chunk(chunk: object) -> str:
    if chunk is None:
        return ""
    contenido = getattr(chunk, "content", None)
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        partes: list[str] = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                t = bloque.get("text")
                if isinstance(t, str):
                    partes.append(t)
        return "".join(partes)
    return ""


async def _tarea_watch_disconnect(req: Request, ev: asyncio.Event) -> None:
    try:
        while True:
            if await req.is_disconnected():
                ev.set()
                return
            await asyncio.sleep(0.25)
    except asyncio.CancelledError:
        return


async def _generador_eventos_sse(
    request: Request,
    grafo: CompiledStateGraph,
    peticion: PeticionAgente,
    usuario: Usuario,
    pool: ConnectionPool,
    bundle: RuntimeAgenteBundle,
) -> AsyncGenerator[dict[str, str], None]:
    disco = asyncio.Event()
    vigia = asyncio.create_task(_tarea_watch_disconnect(request, disco))
    t0 = time.perf_counter()
    texto_acumulado = ""
    modelo_etiqueta = bundle.etiqueta_modelo_compositor.strip()
    t_tool_ini: float | None = None
    ultima_tool_decidida = ""
    abortado_cliente = False
    error_emitido = False

    try:
        try:
            limites_hist = construir_limites_historial(
                bundle.historial_dias_max,
                bundle.historial_turnos_max,
            )
            memoria = MemoriaUsuario(
                peticion.session_id.strip(),
                pool=pool,
                cerrar_conexion_al_salir=False,
                limites=limites_hist,
            )
            entrada: dict[str, Any] = {
                "pregunta": peticion.pregunta.strip(),
                "session_id": peticion.session_id.strip(),
                "primer_turno": bool(peticion.primer_turno),
                "usuario": {
                    "nombre": usuario.nombre,
                    "doc_id": usuario.documento_identidad,
                },
            }
            config = {
                "configurable": {"memoria": memoria, "runtime_agente": bundle},
                "metadata": {
                    # UUID interno de aplicacion (no PII textual); ver decision-5 / TASK-84.
                    "usuario_id_interno": str(usuario.id),
                },
            }
            agen = grafo.astream_events(entrada, version="v2", config=config)
            try:
                async for ev in agen:
                    if disco.is_set():
                        abortado_cliente = True
                        try:
                            await agen.aclose()
                        except Exception:  # noqa: BLE001
                            pass
                        break

                    evento = ev.get("event")
                    nodo = _meta_nodo(ev)

                    if evento == "on_chain_start" and nodo == "ejecutar_tool":
                        t_tool_ini = time.perf_counter()

                    if (
                        evento == "on_chat_model_stream"
                        and nodo == "componer_respuesta"
                    ):
                        datos = (
                            ev.get("data") if isinstance(ev.get("data"), dict) else {}
                        )
                        delta = _extraer_texto_delta_chunk(datos.get("chunk"))
                        if delta:
                            texto_acumulado += delta
                            yield {
                                "event": "token",
                                "data": json.dumps(
                                    EventoToken(
                                        motor="agente", texto=delta
                                    ).model_dump(),
                                ),
                            }

                    if evento == "on_chain_end" and nodo == "decidir_tool":
                        datos = (
                            ev.get("data") if isinstance(ev.get("data"), dict) else {}
                        )
                        salida = datos.get("output")
                        if isinstance(salida, dict):
                            for p in salida.get("pensamientos") or []:
                                if not isinstance(p, dict):
                                    continue
                                if p.get("tipo") != "decision_router":
                                    continue
                                herr = str(p.get("herramienta") or "")
                                ultima_tool_decidida = herr
                                razon = str(p.get("razon_breve") or "")
                                args_sum = p.get("argumentos_resumidos")
                                yield {
                                    "event": "pensamiento",
                                    "data": json.dumps(
                                        EventoPensamiento(
                                            herramienta_candidata=herr,
                                            razon=razon,
                                            argumentos_resumidos=args_sum
                                            if isinstance(args_sum, dict)
                                            else None,
                                        ).model_dump(),
                                    ),
                                }

                    if evento == "on_chain_end" and nodo == "ejecutar_tool":
                        lat_ms = 0
                        if t_tool_ini is not None:
                            lat_ms = int((time.perf_counter() - t_tool_ini) * 1000)
                        datos = (
                            ev.get("data") if isinstance(ev.get("data"), dict) else {}
                        )
                        salida = datos.get("output")
                        nombre_tool = ultima_tool_decidida or "tool"
                        if isinstance(salida, dict) and salida.get("tool_decidida"):
                            nombre_tool = str(
                                salida.get("tool_decidida") or nombre_tool
                            )
                        resultado_listado: dict[str, Any] | None = None
                        if isinstance(salida, dict):
                            rt = salida.get("resultado_tool")
                            if (
                                isinstance(rt, dict)
                                and "conteo" in rt
                                and isinstance(rt.get("items"), list)
                            ):
                                items = rt.get("items") or []
                                items_muestra = (
                                    items[:50] if isinstance(items, list) else []
                                )
                                resultado_listado = {
                                    "conteo": rt.get("conteo"),
                                    "muestra_truncada": rt.get("muestra_truncada"),
                                    "items": items_muestra,
                                    "filtros_aplicados": rt.get("filtros_aplicados"),
                                }
                        if isinstance(salida, dict):
                            fuentes = salida.get("fuentes")
                            if isinstance(fuentes, list) and fuentes:
                                serializables = [
                                    f for f in fuentes if isinstance(f, dict)
                                ]
                                yield {
                                    "event": "fuentes",
                                    "data": json.dumps(
                                        EventoFuentes(
                                            chunks=serializables
                                        ).model_dump(),
                                    ),
                                }
                        faq_match: bool | None = None
                        faq_umbral: float | None = None
                        faq_consulta: str | None = None
                        if nombre_tool == "faq_estructurada" and isinstance(
                            salida, dict
                        ):
                            plist = salida.get("pensamientos")
                            if isinstance(plist, list):
                                for pen in plist:
                                    if not isinstance(pen, dict):
                                        continue
                                    if pen.get("tipo") != "ejecucion_tool":
                                        continue
                                    v_match = pen.get("faq_match_encontrado")
                                    if isinstance(v_match, bool):
                                        faq_match = v_match
                                    v_um = pen.get("faq_umbral_match")
                                    try:
                                        faq_umbral = (
                                            float(v_um) if v_um is not None else None
                                        )
                                    except (TypeError, ValueError):
                                        faq_umbral = None
                                    v_cq = pen.get("faq_consulta_ejecutada")
                                    faq_consulta = (
                                        str(v_cq) if v_cq is not None else None
                                    )
                                    break
                        yield {
                            "event": "herramienta",
                            "data": json.dumps(
                                EventoHerramienta(
                                    nombre=nombre_tool,
                                    latencia_ms=lat_ms,
                                    faq_match_encontrado=faq_match,
                                    faq_umbral_match=faq_umbral,
                                    faq_consulta_ejecutada=faq_consulta,
                                    resultado_listado=resultado_listado,
                                ).model_dump(exclude_none=True),
                            ),
                        }
                        t_tool_ini = None

            except asyncio.CancelledError:
                raise
            except MemoriaConexionError as exc:
                error_emitido = True
                yield {
                    "event": "error",
                    "data": json.dumps(
                        EventoError(
                            codigo="memoria_postgres",
                            mensaje=str(exc),
                            motor="agente",
                        ).model_dump(),
                    ),
                }
            except Exception as exc:  # noqa: BLE001 — SSE: error seguro al cliente
                error_emitido = True
                logger.exception("Fallo en streaming del agente")
                yield {
                    "event": "error",
                    "data": json.dumps(
                        EventoError(
                            codigo="agente_error",
                            mensaje="No se pudo completar la respuesta del agente. Intente de nuevo.",
                            motor="agente",
                        ).model_dump(),
                    ),
                }
                logger.debug("Detalle interno del fallo del agente: %s", exc)

            if not abortado_cliente and not error_emitido:
                lat_total = int((time.perf_counter() - t0) * 1000)
                yield {
                    "event": "final",
                    "data": json.dumps(
                        EventoFinal(
                            motor="agente",
                            texto=texto_acumulado,
                            latencia_ms=lat_total,
                            modelo=modelo_etiqueta,
                            metricas=None,
                        ).model_dump(),
                    ),
                }
        except MemoriaConexionError as exc:
            error_emitido = True
            yield {
                "event": "error",
                "data": json.dumps(
                    EventoError(
                        codigo="memoria_postgres",
                        mensaje=str(exc),
                        motor="agente",
                    ).model_dump(),
                ),
            }

    finally:
        vigia.cancel()


@router.post(
    "/agente/stream",
    summary="Streaming SSE del agente conversacional",
    description=(
        "Emite eventos Server-Sent Events JSON: `pensamiento` (incluye `argumentos_resumidos` "
        "opcional del router), `herramienta` (diagnosticos opcionales FAQ: `faq_match_encontrado`, "
        "`faq_umbral_match`, `faq_consulta_ejecutada`), `token`, "
        "`fuentes`, `final` y `error`. Requiere sesion valida (cookie o cabecera) alineada "
        "con el campo `session_id` del cuerpo."
    ),
    responses={
        200: {
            "description": "Flujo SSE (`text/event-stream`).",
            "content": {"text/event-stream": {}},
        },
        403: {"description": "session_id no coincide con la sesion autenticada."},
        503: {
            "description": "Grafo del agente no disponible (configuracion o dependencias)."
        },
    },
)
async def agente_stream(
    request: Request,
    peticion: PeticionAgente,
    usuario: Usuario = Depends(obtener_usuario_actual),
    grafo: CompiledStateGraph = Depends(obtener_grafo_agente),
    pool: ConnectionPool = Depends(obtener_pool_memoria_psycopg),
    bundle: RuntimeAgenteBundle = Depends(obtener_bundle_runtime_agente),
) -> EventSourceResponse:
    """SSE extendido del agente (LangGraph + memoria Postgres + tools)."""
    _session_id_autorizado(peticion, usuario)
    return EventSourceResponse(
        _generador_eventos_sse(request, grafo, peticion, usuario, pool, bundle),
        ping=_KEEPALIVE_SEG,
    )


__all__ = ["router"]
