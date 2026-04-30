"""Concurrencia: ``num_ctx`` por petición sin pisar configuración global del cliente."""

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
    modelo="test",
    score_recuperacion=1.0,
    latencia_ms=10,
    prompt_sistema_usado="demo",
    fuentes_bm25=(),
)


@pytest.mark.asyncio
async def test_streams_concurrentes_respetan_num_ctx_sin_corromper_singleton(
    async_client: AsyncClient,
) -> None:
    pipeline_mock = getattr(async_client, "_pipeline_mock", None)
    assert pipeline_mock is not None
    valores_num_ctx: list[int | None] = []

    def _stream_desde_ctx(*_args: object, **kwargs: object):
        nc = kwargs.get("num_ctx")
        assert isinstance(nc, int)
        valores_num_ctx.append(nc)
        yield "delta", None
        yield _RESP_CORTA.texto, _RESP_CORTA

    pipeline_mock.stream_ollama_desde_contexto.side_effect = _stream_desde_ctx
    inicial = pipeline_mock._cliente.configuracion.num_ctx

    async def leer_stream(num_ctx: int) -> None:
        async with async_client.stream(
            "POST",
            "/api/qa/stream",
            json={
                "pregunta": "¿Concurrente?",
                "usar_ollama": True,
                "usar_openai": False,
                "num_ctx": num_ctx,
            },
        ) as response:
            assert response.status_code == 200
            await response.aread()

    await asyncio.gather(leer_stream(4096), leer_stream(32768))

    assert {4096, 32768}.issubset(set(valores_num_ctx))
    assert pipeline_mock._cliente.configuracion.num_ctx == inicial
