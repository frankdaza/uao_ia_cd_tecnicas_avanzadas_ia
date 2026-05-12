"""Concurrencia: temperatura y top_p por petición en streaming OpenAI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from httpx import AsyncClient

from src.qa.pipeline import RespuestaQa

_RESP_CORTA = RespuestaQa(
    texto="Listo.",
    archivo_fuente=Path("demo.md"),
    source_url="https://example.invalid/",
    titulo="Demo",
    modelo="gpt-4o-mini",
    score_recuperacion=1.0,
    latencia_ms=10,
    prompt_sistema_usado="demo",
    fuentes_bm25=(),
)


@pytest.mark.asyncio
async def test_streams_concurrentes_respetan_temperatura_sin_corromper_singleton(
    async_client: AsyncClient,
) -> None:
    pipeline_mock = getattr(async_client, "_pipeline_mock", None)
    assert pipeline_mock is not None
    valores_temperatura: list[float] = []

    def _stream_desde_ctx(*_args: object, **kwargs: object):
        t = kwargs.get("temperatura")
        assert isinstance(t, float)
        valores_temperatura.append(t)
        yield "delta", None
        yield _RESP_CORTA.texto, _RESP_CORTA

    pipeline_mock.stream_openai_desde_contexto.side_effect = _stream_desde_ctx

    async def leer_stream(temperatura: float) -> None:
        async with async_client.stream(
            "POST",
            "/api/qa/stream",
            json={
                "pregunta": "¿Concurrente?",
                "temperatura": temperatura,
                "top_p": 1.0,
            },
        ) as response:
            assert response.status_code == 200
            await response.aread()

    await asyncio.gather(leer_stream(0.1), leer_stream(0.9))

    assert {0.1, 0.9}.issubset(set(valores_temperatura))
