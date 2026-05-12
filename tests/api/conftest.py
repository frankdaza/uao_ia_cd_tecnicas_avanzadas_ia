"""Fixtures para los tests del API FastAPI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import crear_app
from src.qa.pipeline import ContextoInferencia, FuenteBm25, RespuestaQa
from src.retrieval.recuperador import DocumentoRecuperado


# ---------------------------------------------------------------------------
# Helpers de fixtures
# ---------------------------------------------------------------------------

_DOCUMENTO_MOCK = DocumentoRecuperado(
    ruta=Path("urgencias.md"),
    titulo="Urgencias",
    source_url="https://valledellili.org/urgencias/",
    contenido="# Urgencias\nContenido demo.",
    score=12.45,
)

_RESPUESTA_OLLAMA = RespuestaQa(
    texto="La Fundación Valle del Lili ofrece servicios de urgencias 24 horas.",
    archivo_fuente=Path("urgencias.md"),
    source_url="https://valledellili.org/urgencias/",
    titulo="Urgencias",
    modelo="gpt-4o-mini",
    score_recuperacion=12.45,
    latencia_ms=1200,
    prompt_sistema_usado="Eres un asistente...",
    fuentes_bm25=(
        FuenteBm25(
            ruta=Path("urgencias.md"),
            titulo="Urgencias",
            source_url="https://valledellili.org/urgencias/",
            score=12.45,
        ),
    ),
)


def _crear_pipeline_mock() -> MagicMock:
    """Pipeline simulado para tests sin red real ni modelos LLM."""
    pipeline = MagicMock()

    # Propiedad recuperador
    recuperador = MagicMock()
    pipeline.recuperador = recuperador

    # Propiedad cliente_openai
    cliente_openai = MagicMock()
    cliente_openai.configuracion.tiene_api_key.return_value = True
    pipeline.cliente_openai = cliente_openai

    # Métodos sincronicos
    pipeline.responder.return_value = _RESPUESTA_OLLAMA
    pipeline.responder_openai.return_value = _RESPUESTA_OLLAMA
    pipeline.responder_dual.return_value = (_RESPUESTA_OLLAMA, _RESPUESTA_OLLAMA)

    # Stream: genera un token y el final
    def _fake_stream(*_args, **_kwargs):
        yield "La Fundación", None
        yield _RESPUESTA_OLLAMA.texto, _RESPUESTA_OLLAMA

    pipeline.responder_stream.side_effect = _fake_stream
    pipeline.responder_openai_stream.side_effect = _fake_stream

    ctx = ContextoInferencia(
        vacio=False,
        mensajes=[],
        documentos=(_DOCUMENTO_MOCK,),
        prompt_sistema_usado="Eres un asistente...",
    )
    pipeline.preparar_contexto_inferencia.return_value = ctx
    pipeline.stream_ollama_desde_contexto.side_effect = _fake_stream
    pipeline.stream_openai_desde_contexto.side_effect = _fake_stream

    # Configuracion del cliente Ollama
    pipeline._cliente.configuracion.num_ctx = 8192

    return pipeline


@pytest_asyncio.fixture
async def async_client():
    """Cliente HTTP asincrónico con ASGI transport (sin red real)."""
    app = crear_app()
    _pipeline = _crear_pipeline_mock()
    app.state.pipeline = _pipeline
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client._pipeline_mock = _pipeline  # type: ignore[attr-defined]
        yield client
