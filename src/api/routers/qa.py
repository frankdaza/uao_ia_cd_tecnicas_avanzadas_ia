"""
Endpoints Q&A: sincrónico y SSE (streaming).

- POST /api/qa            — respuesta sincrónica (Ollama / OpenAI / dual)
- POST /api/qa/stream     — SSE para un motor activo
- POST /api/qa/dual/stream — SSE secuencial Ollama → OpenAI con una sola pasada BM25
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from src.api.dependencias import obtener_pipeline
from src.api.esquemas import (
    EventoError,
    EventoFinal,
    EventoFuentes,
    EventoToken,
    FuenteRespuesta,
    MetadatosMotor,
    PeticionQa,
    RespuestaQa,
)
from src.api.sse_iteracion import async_iter_desde_factory
from src.qa.cliente_ollama import ModeloNoDisponibleError, OllamaNoAccesibleError
from src.qa.cliente_openai import ClaveApiOpenAiAusenteError, OpenAiClienteError
from src.qa.pipeline import PipelineQa, RespuestaQa as ResultadoInferencia
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO
from src.retrieval.recuperador import DocumentoRecuperado

router = APIRouter(tags=["qa"])

_KEEPALIVE_SEG = 15


# ---------------------------------------------------------------------------
# Utilidades de serialización
# ---------------------------------------------------------------------------


def _serializar_fuentes_desde_bm25(pipeline_result: object) -> list[FuenteRespuesta]:
    """Convierte fuentes BM25 de RespuestaQa del pipeline en esquemas del API."""
    fuentes: list[FuenteRespuesta] = []
    for f in pipeline_result.fuentes_bm25:
        fuentes.append(
            FuenteRespuesta(
                archivo=f.ruta.name,
                titulo=f.titulo or "",
                source_url=f.source_url or "",
                score=f.score,
            )
        )
    return fuentes


def _fuentes_desde_documentos(
    documentos: tuple[DocumentoRecuperado, ...],
) -> list[FuenteRespuesta]:
    """Construye lista de fuentes desde documentos recuperados (antes del LLM)."""
    return [
        FuenteRespuesta(
            archivo=d.ruta.name,
            titulo=d.titulo or "",
            source_url=d.source_url or "",
            score=d.score,
        )
        for d in documentos
    ]


def _prompt_efectivo(peticion: PeticionQa) -> str:
    return peticion.prompt_sistema if peticion.prompt_sistema else PROMPT_SISTEMA_DEFECTO


# ---------------------------------------------------------------------------
# Endpoint sincrónico POST /api/qa
# ---------------------------------------------------------------------------


@router.post("/qa", response_model=RespuestaQa)
async def qa_sincrono(
    peticion: PeticionQa,
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> RespuestaQa:
    """Respuesta Q&A sincrónica (sin streaming). Soporta Ollama, OpenAI o ambos."""
    if not peticion.usar_ollama and not peticion.usar_openai:
        raise HTTPException(
            status_code=400,
            detail="Debes activar al menos un motor de generación (usar_ollama o usar_openai).",
        )

    ps = _prompt_efectivo(peticion)

    texto_ollama: str | None = None
    texto_openai: str | None = None
    meta_ollama: MetadatosMotor | None = None
    meta_openai: MetadatosMotor | None = None
    fuentes: list[FuenteRespuesta] = []

    def _ejecutar() -> tuple[str | None, str | None, MetadatosMotor | None, MetadatosMotor | None, list[FuenteRespuesta]]:
        nonlocal texto_ollama, texto_openai, meta_ollama, meta_openai, fuentes

        if peticion.usar_ollama and peticion.usar_openai:
            # Modo dual: una pasada BM25
            try:
                res_o, res_oa = pipeline.responder_dual(
                    pregunta=peticion.pregunta,
                    usar_ollama=True,
                    usar_openai=True,
                    modelo_ollama=peticion.modelo_ollama,
                    modelo_openai=peticion.modelo_openai,
                    prompt_sistema=ps,
                    max_completion_tokens=peticion.max_tokens_openai,
                    num_ctx=peticion.num_ctx,
                )
                assert res_o is not None and res_oa is not None
                fuentes = _serializar_fuentes_desde_bm25(res_o)
                return (
                    res_o.texto,
                    res_oa.texto,
                    MetadatosMotor(modelo=res_o.modelo, latencia_ms=res_o.latencia_ms),
                    MetadatosMotor(modelo=res_oa.modelo, latencia_ms=res_oa.latencia_ms),
                    fuentes,
                )
            except OllamaNoAccesibleError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            except ModeloNoDisponibleError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except (ClaveApiOpenAiAusenteError, OpenAiClienteError) as exc:
                raise HTTPException(status_code=402, detail=str(exc)) from exc

        if peticion.usar_ollama:
            try:
                res = pipeline.responder(
                    pregunta=peticion.pregunta,
                    modelo=peticion.modelo_ollama,
                    prompt_sistema=ps,
                    num_ctx=peticion.num_ctx,
                )
                fuentes = _serializar_fuentes_desde_bm25(res)
                return (
                    res.texto,
                    None,
                    MetadatosMotor(modelo=res.modelo, latencia_ms=res.latencia_ms),
                    None,
                    fuentes,
                )
            except OllamaNoAccesibleError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            except ModeloNoDisponibleError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        # Solo OpenAI
        try:
            res = pipeline.responder_openai(
                pregunta=peticion.pregunta,
                modelo_openai=peticion.modelo_openai,
                prompt_sistema=ps,
                max_completion_tokens=peticion.max_tokens_openai,
            )
            fuentes = _serializar_fuentes_desde_bm25(res)
            return (
                None,
                res.texto,
                None,
                MetadatosMotor(modelo=res.modelo, latencia_ms=res.latencia_ms),
                fuentes,
            )
        except (ClaveApiOpenAiAusenteError, OpenAiClienteError) as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from exc

    texto_ollama, texto_openai, meta_ollama, meta_openai, fuentes = await asyncio.to_thread(
        _ejecutar,
    )

    return RespuestaQa(
        texto_ollama=texto_ollama,
        texto_openai=texto_openai,
        fuentes=fuentes,
        metadatos_ollama=meta_ollama,
        metadatos_openai=meta_openai,
    )


async def _tarea_watch_disconnect(req: Request, ev: asyncio.Event) -> None:
    """Marca ``ev`` si el cliente cierra la conexión SSE."""
    try:
        while True:
            if await req.is_disconnected():
                ev.set()
                return
            await asyncio.sleep(0.25)
    except asyncio.CancelledError:
        return


async def _emitir_eventos_sse_stream(
    motor: str,
    agen: AsyncGenerator[object, None],
    *,
    documentos_bm25_previos: tuple[DocumentoRecuperado, ...] | None,
    emitir_fuentes_post_final: bool = True,
) -> AsyncGenerator[dict, None]:
    """
    Consume `(texto_acumulado, ResultadoInferencia | None)` del streaming sincrono
    y emite SSE `token` (solo el delta nuevo), `final` y ``fuentes`` del resultado final.

    Si ``documentos_bm25_previos`` no es vacio, emite un evento ``fuentes`` antes del
    primer token (transparencia pre-LLM).
    """
    if documentos_bm25_previos is not None and len(documentos_bm25_previos) > 0:
        yield {"event": "fuentes", "data": json.dumps(
            EventoFuentes(fuentes=_fuentes_desde_documentos(documentos_bm25_previos)).model_dump(),
        )}

    texto_previo_acumulado = ""
    resultado_final = None

    async for elemento in agen:
        if isinstance(elemento, BaseException):
            yield {"event": "error", "data": json.dumps(
                EventoError(motor=motor, mensaje=str(elemento)).model_dump(),
            )}
            return

        if not isinstance(elemento, tuple) or len(elemento) != 2:
            yield {"event": "error", "data": json.dumps(
                EventoError(motor=motor, mensaje="Evento SSE interno corrupto").model_dump(),
            )}
            return

        texto_acumulado, final_resp = elemento  # type: ignore[misc]
        tac = str(texto_acumulado)
        if final_resp is None:
            nuevo = tac[len(texto_previo_acumulado) :]
            texto_previo_acumulado = tac
            if nuevo:
                yield {"event": "token", "data": json.dumps(
                    EventoToken(motor=motor, texto=nuevo).model_dump(),
                )}
            continue

        # Ultima tupla: puede llevar texto acumulado distinto del ultimo token
        nuevo = tac[len(texto_previo_acumulado) :]
        texto_previo_acumulado = tac
        if nuevo:
            yield {"event": "token", "data": json.dumps(
                EventoToken(motor=motor, texto=nuevo).model_dump(),
            )}
        resultado_final = final_resp  # ResultadoInferencia

    if resultado_final is None:
        return

    yield {"event": "final", "data": json.dumps(
        EventoFinal(
            motor=motor,
            texto=resultado_final.texto,
            latencia_ms=resultado_final.latencia_ms,
            modelo=resultado_final.modelo,
        ).model_dump(),
    )}
    if emitir_fuentes_post_final:
        yield {"event": "fuentes", "data": json.dumps(
            EventoFuentes(fuentes=_serializar_fuentes_desde_bm25(resultado_final)).model_dump(),
        )}


def _inferencia_bm25_vacia(
    prompt_sistema: str,
    modelo_etiqueta: str,
    t_inicio: float,
) -> ResultadoInferencia:
    """Replica el mensaje cuando no hay documentos recuperados (alineado con el pipeline)."""
    latencia_ms = int((time.perf_counter() - t_inicio) * 1000)
    return ResultadoInferencia(
        texto="No tengo información suficiente",
        archivo_fuente=None,
        source_url="",
        titulo="",
        modelo=modelo_etiqueta,
        score_recuperacion=0.0,
        latencia_ms=latencia_ms,
        prompt_sistema_usado=prompt_sistema,
        fuentes_bm25=(),
    )


async def _stream_ollama(
    request: Request,
    pipeline: PipelineQa,
    peticion: PeticionQa,
) -> AsyncGenerator[dict, None]:
    ps = _prompt_efectivo(peticion)
    disco = asyncio.Event()
    vigia = asyncio.create_task(_tarea_watch_disconnect(request, disco))

    ctx = await asyncio.to_thread(pipeline.preparar_contexto_inferencia, peticion.pregunta, ps)

    try:
        if ctx.vacio:
            t_ini = time.perf_counter()
            rf = await asyncio.to_thread(
                lambda: _inferencia_bm25_vacia(
                    ps,
                    peticion.modelo_ollama,
                    t_ini,
                ),
            )

            texto = rf.texto
            yield {"event": "token", "data": json.dumps(
                EventoToken(motor="ollama", texto=texto).model_dump(),
            )}
            yield {"event": "final", "data": json.dumps(
                EventoFinal(
                    motor="ollama",
                    texto=rf.texto,
                    latencia_ms=rf.latencia_ms,
                    modelo=rf.modelo,
                ).model_dump(),
            )}
            yield {"event": "fuentes", "data": json.dumps(
                EventoFuentes(fuentes=[]).model_dump(),
            )}
            return

        t_llm = time.perf_counter()

        def factory_ollama():
            return pipeline.stream_ollama_desde_contexto(
                ctx,
                peticion.modelo_ollama,
                t_llm,
                num_ctx=peticion.num_ctx,
            )

        agen = async_iter_desde_factory(factory_ollama, disconnect_event=disco)
        async for ev in _emitir_eventos_sse_stream(
            "ollama",
            agen,
            documentos_bm25_previos=ctx.documentos,
            emitir_fuentes_post_final=False,
        ):
            yield ev

    finally:
        vigia.cancel()
        await asyncio.sleep(0)


async def _stream_openai(
    request: Request,
    pipeline: PipelineQa,
    peticion: PeticionQa,
) -> AsyncGenerator[dict, None]:
    ps = _prompt_efectivo(peticion)
    disco = asyncio.Event()
    vigia = asyncio.create_task(_tarea_watch_disconnect(request, disco))

    ctx = await asyncio.to_thread(pipeline.preparar_contexto_inferencia, peticion.pregunta, ps)

    try:
        if ctx.vacio:
            t_ini = time.perf_counter()
            rf = await asyncio.to_thread(
                lambda: _inferencia_bm25_vacia(
                    ps,
                    peticion.modelo_openai,
                    t_ini,
                ),
            )
            texto = rf.texto
            yield {"event": "token", "data": json.dumps(
                EventoToken(motor="openai", texto=texto).model_dump(),
            )}
            yield {"event": "final", "data": json.dumps(
                EventoFinal(
                    motor="openai",
                    texto=rf.texto,
                    latencia_ms=rf.latencia_ms,
                    modelo=rf.modelo,
                ).model_dump(),
            )}
            yield {"event": "fuentes", "data": json.dumps(
                EventoFuentes(fuentes=[]).model_dump(),
            )}
            return

        t_llm = time.perf_counter()

        def factory_openai():
            return pipeline.stream_openai_desde_contexto(
                ctx,
                peticion.modelo_openai,
                t_llm,
                max_completion_tokens=peticion.max_tokens_openai,
            )

        agen = async_iter_desde_factory(factory_openai, disconnect_event=disco)
        async for ev in _emitir_eventos_sse_stream(
            "openai",
            agen,
            documentos_bm25_previos=ctx.documentos,
            emitir_fuentes_post_final=False,
        ):
            yield ev

    finally:
        vigia.cancel()
        await asyncio.sleep(0)


async def _stream_dual(
    request: Request,
    pipeline: PipelineQa,
    peticion: PeticionQa,
) -> AsyncGenerator[dict, None]:
    """SSE secuencial Ollama luego OpenAI con una pasada BM25."""
    ps = _prompt_efectivo(peticion)
    disco = asyncio.Event()
    vigia = asyncio.create_task(_tarea_watch_disconnect(request, disco))

    ctx = await asyncio.to_thread(pipeline.preparar_contexto_inferencia, peticion.pregunta, ps)

    try:
        if ctx.vacio:
            t_ini = time.perf_counter()
            modelo_o = peticion.modelo_ollama
            modelo_a = peticion.modelo_openai

            rf_o = await asyncio.to_thread(lambda: _inferencia_bm25_vacia(ps, modelo_o, t_ini))
            texto_o = rf_o.texto
            yield {"event": "token", "data": json.dumps(
                EventoToken(motor="ollama", texto=texto_o).model_dump(),
            )}
            yield {"event": "final", "data": json.dumps(
                EventoFinal(
                    motor="ollama",
                    texto=rf_o.texto,
                    latencia_ms=rf_o.latencia_ms,
                    modelo=rf_o.modelo,
                ).model_dump(),
            )}
            yield {"event": "fuentes", "data": json.dumps(
                EventoFuentes(fuentes=[]).model_dump(),
            )}

            rf_a = await asyncio.to_thread(
                lambda: _inferencia_bm25_vacia(
                    ps,
                    modelo_a,
                    time.perf_counter(),
                ),
            )
            texto_a = rf_a.texto
            yield {"event": "token", "data": json.dumps(
                EventoToken(motor="openai", texto=texto_a).model_dump(),
            )}
            yield {"event": "final", "data": json.dumps(
                EventoFinal(
                    motor="openai",
                    texto=rf_a.texto,
                    latencia_ms=rf_a.latencia_ms,
                    modelo=rf_a.modelo,
                ).model_dump(),
            )}
            yield {"event": "fuentes", "data": json.dumps(
                EventoFuentes(fuentes=[]).model_dump(),
            )}
            return

        docs = ctx.documentos
        yield {"event": "fuentes", "data": json.dumps(
            EventoFuentes(fuentes=_fuentes_desde_documentos(docs)).model_dump(),
        )}

        t_ollama = time.perf_counter()

        def factory_o():
            return pipeline.stream_ollama_desde_contexto(
                ctx,
                peticion.modelo_ollama,
                t_ollama,
                num_ctx=peticion.num_ctx,
            )

        agen_o = async_iter_desde_factory(factory_o, disconnect_event=disco)

        async for ev in _emitir_eventos_sse_stream(
            "ollama",
            agen_o,
            documentos_bm25_previos=None,
            emitir_fuentes_post_final=False,
        ):
            yield ev

        t_openai = time.perf_counter()

        def factory_a():
            return pipeline.stream_openai_desde_contexto(
                ctx,
                peticion.modelo_openai,
                t_openai,
                max_completion_tokens=peticion.max_tokens_openai,
            )

        agen_a = async_iter_desde_factory(factory_a, disconnect_event=disco)

        async for ev in _emitir_eventos_sse_stream(
            "openai",
            agen_a,
            documentos_bm25_previos=None,
            emitir_fuentes_post_final=False,
        ):
            yield ev

    finally:
        vigia.cancel()
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# Endpoints SSE
# ---------------------------------------------------------------------------


@router.post("/qa/stream")
async def qa_stream(
    request: Request,
    peticion: PeticionQa,
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> EventSourceResponse:
    """SSE: streaming token a token para Ollama o OpenAI (uno activo a la vez)."""
    if not peticion.usar_ollama and not peticion.usar_openai:
        raise HTTPException(
            status_code=400,
            detail="Debes activar al menos un motor (usar_ollama o usar_openai).",
        )
    if peticion.usar_ollama and peticion.usar_openai:
        raise HTTPException(
            status_code=400,
            detail="Para modo dual usa POST /api/qa/dual/stream.",
        )

    gen = (
        _stream_ollama(request, pipeline, peticion)
        if peticion.usar_ollama
        else _stream_openai(request, pipeline, peticion)
    )
    return EventSourceResponse(gen, ping=_KEEPALIVE_SEG)


@router.post("/qa/dual/stream")
async def qa_dual_stream(
    request: Request,
    peticion: PeticionQa,
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> EventSourceResponse:
    """SSE secuencial Ollama hasta OpenAI con una sola pasada BM25."""
    if not peticion.usar_ollama or not peticion.usar_openai:
        raise HTTPException(
            status_code=400,
            detail="El modo dual requiere usar_ollama=true y usar_openai=true.",
        )
    return EventSourceResponse(_stream_dual(request, pipeline, peticion), ping=_KEEPALIVE_SEG)
