"""Tests de los endpoints SSE: POST /api/qa/stream y /api/qa/dual/stream."""

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
async def test_stream_ollama_emite_eventos(async_client: AsyncClient) -> None:
    """POST /api/qa/stream emite eventos SSE parseables para Ollama."""
    async with async_client.stream(
        "POST",
        "/api/qa/stream",
        json={"pregunta": "¿Qué hace la FVL?", "usar_ollama": True, "usar_openai": False},
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
async def test_stream_requiere_al_menos_un_motor(async_client: AsyncClient) -> None:
    """Sin motores activos retorna 400."""
    response = await async_client.post(
        "/api/qa/stream",
        json={"pregunta": "¿Qué es la FVL?", "usar_ollama": False, "usar_openai": False},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stream_dual_requiere_ambos_motores(async_client: AsyncClient) -> None:
    """El endpoint dual requiere usar_ollama=true y usar_openai=true."""
    response = await async_client.post(
        "/api/qa/dual/stream",
        json={"pregunta": "¿Qué es la FVL?", "usar_ollama": True, "usar_openai": False},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stream_dual_emite_eventos_con_motor(async_client: AsyncClient) -> None:
    """POST /api/qa/dual/stream emite eventos con campo motor."""
    async with async_client.stream(
        "POST",
        "/api/qa/dual/stream",
        json={"pregunta": "¿Qué hace la FVL?", "usar_ollama": True, "usar_openai": True},
    ) as response:
        assert response.status_code == 200
        cuerpo = await response.aread()

    texto = cuerpo.decode("utf-8")
    eventos = _parsear_eventos_sse(texto)
    motores = {e.get("motor") for e in eventos if "motor" in e}
    assert motores  # Al menos un motor emitió eventos
