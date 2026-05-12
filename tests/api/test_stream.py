"""Tests del endpoint SSE POST /api/qa/stream."""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient


def _parsear_eventos_sse(texto: str) -> list[dict]:
    """Extrae los dicts de datos de una respuesta SSE cruda."""
    eventos = []
    for linea in texto.splitlines():
        if linea.startswith("data: "):
            try:
                eventos.append(json.loads(linea[6:]))
            except json.JSONDecodeError:
                pass
    return eventos


@pytest.mark.asyncio
async def test_stream_openai_emite_eventos(async_client: AsyncClient) -> None:
    """POST /api/qa/stream emite eventos SSE parseables para OpenAI."""
    async with async_client.stream(
        "POST",
        "/api/qa/stream",
        json={"pregunta": "¿Qué hace la FVL?"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        cuerpo = await response.aread()

    texto = cuerpo.decode("utf-8")
    eventos = _parsear_eventos_sse(texto)
    tipos_por_indice = [e.get("tipo") for e in eventos]

    primer_token_o_final = None
    for i, tipo in enumerate(tipos_por_indice):
        if tipo == "token" or tipo == "final":
            primer_token_o_final = i
            break
    assert primer_token_o_final is not None

    if "fuentes" in tipos_por_indice:
        assert tipos_por_indice.index("fuentes") < primer_token_o_final


@pytest.mark.asyncio
async def test_stream_requiere_openai_key(async_client: AsyncClient) -> None:
    """Sin OPENAI_API_KEY el streaming responde 402."""
    async_client._pipeline_mock.cliente_openai.configuracion.tiene_api_key.return_value = (  # type: ignore[attr-defined]
        False
    )
    response = await async_client.post(
        "/api/qa/stream",
        json={"pregunta": "¿Qué es la FVL?"},
    )
    assert response.status_code == 402
    async_client._pipeline_mock.cliente_openai.configuracion.tiene_api_key.return_value = (  # type: ignore[attr-defined]
        True
    )


@pytest.mark.asyncio
async def test_stream_eventos_usan_motor_openai(async_client: AsyncClient) -> None:
    """Los eventos con campo motor usan openai."""
    async with async_client.stream(
        "POST",
        "/api/qa/stream",
        json={"pregunta": "¿Qué hace la FVL?"},
    ) as response:
        assert response.status_code == 200
        cuerpo = await response.aread()

    texto = cuerpo.decode("utf-8")
    eventos = _parsear_eventos_sse(texto)
    motores = {e.get("motor") for e in eventos if "motor" in e}
    assert motores == {"openai"}
