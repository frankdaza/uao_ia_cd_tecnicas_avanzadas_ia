"""
Endpoints Q&A: sincrónico y SSE (streaming) vía OpenAI.
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


def _asegurar_openai_configurado(pipeline: PipelineQa) -> None:
    if pipeline.cliente_openai is None:
        raise HTTPException(
            status_code=503,
            detail="El servidor no tiene configurado el cliente OpenAI.",
        )
    if not pipeline.cliente_openai.configuracion.tiene_api_key():
        raise HTTPException(
            status_code=402,
            detail=(
                "Configura una clave API válida en la variable OPENAI_API_KEY dentro del "
                "archivo .env (en la raíz del proyecto)."
            ),
        )


# ---------------------------------------------------------------------------
# Endpoint sincrónico POST /api/qa
# ---------------------------------------------------------------------------


@router.post("/qa", response_model=RespuestaQa)
async def qa_sincrono(
    peticion: PeticionQa,
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> RespuestaQa:
    """Respuesta Q&A sincrónica (sin streaming) vía OpenAI."""
    _asegurar_openai_configurado(pipeline)

    ps = _prompt_efectivo(peticion)

    def _ejecutar() -> tuple[str | None, str | None, MetadatosMotor | None, MetadatosMotor | None, list[FuenteRespuesta]]:
        try:
            res = pipeline.responder_openai(
                pregunta=peticion.pregunta,
                modelo_openai=peticion.modelo_openai,
                prompt_sistema=ps,
                max_completion_tokens=peticion.max_tokens_openai,
                temperatura=peticion.temperatura,
                top_p=peticion.top_p,
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
            yield {"event": "token", "data": json.dumps(
                EventoToken(motor="openai", texto=rf.texto).model_dump(),
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
                temperatura=peticion.temperatura,
                top_p=peticion.top_p,
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


# ---------------------------------------------------------------------------
# Endpoints SSE
# ---------------------------------------------------------------------------


@router.post("/qa/stream")
async def qa_stream(
    request: Request,
    peticion: PeticionQa,
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> EventSourceResponse:
    """SSE: streaming token a token vía OpenAI."""
    _asegurar_openai_configurado(pipeline)
    return EventSourceResponse(_stream_openai(request, pipeline, peticion), ping=_KEEPALIVE_SEG)
