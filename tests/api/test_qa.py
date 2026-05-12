"""Tests del endpoint POST /api/qa (sincrónico)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from src.qa.cliente_openai import OpenAiClienteError


@pytest.mark.asyncio
async def test_qa_solo_openai(async_client: AsyncClient) -> None:
    """POST /api/qa retorna texto_openai y fuentes."""
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Cuáles son los servicios de urgencias?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["texto_ollama"] is None
    assert data["texto_openai"] is not None
    assert isinstance(data["fuentes"], list)
    assert data["metadatos_ollama"] is None
    assert data["metadatos_openai"] is not None


@pytest.mark.asyncio
async def test_qa_pregunta_vacia_rechazada(async_client: AsyncClient) -> None:
    """Una pregunta vacía devuelve 422 (validación Pydantic)."""
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_qa_sin_openai_key(async_client: AsyncClient) -> None:
    """Sin OPENAI_API_KEY el endpoint sincrónico responde 402."""
    async_client._pipeline_mock.cliente_openai.configuracion.tiene_api_key.return_value = (  # type: ignore[attr-defined]
        False
    )
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Qué es la FVL?"},
    )
    assert response.status_code == 402
    async_client._pipeline_mock.cliente_openai.configuracion.tiene_api_key.return_value = (  # type: ignore[attr-defined]
        True
    )


@pytest.mark.asyncio
async def test_qa_openai_error(async_client: AsyncClient) -> None:
    """Errores del cliente OpenAI se exponen como 402 sin traceback."""
    async_client._pipeline_mock.responder_openai.side_effect = OpenAiClienteError(  # type: ignore[attr-defined]
        "Error de conexión demo",
    )
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Qué es la FVL?"},
    )
    assert response.status_code == 402
    body = response.json()
    assert "detail" in body
    assert "traceback" not in str(body).lower()
    async_client._pipeline_mock.responder_openai.side_effect = None  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_qa_fuentes_en_respuesta(async_client: AsyncClient) -> None:
    """La respuesta incluye fuentes BM25 con los campos requeridos."""
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Cuál es la misión de la FVL?"},
    )
    assert response.status_code == 200
    data = response.json()
    if data["fuentes"]:
        fuente = data["fuentes"][0]
        assert "archivo" in fuente
        assert "score" in fuente
        assert "source_url" in fuente


@pytest.mark.asyncio
async def test_qa_pasa_temperatura_y_top_p_al_pipeline(async_client: AsyncClient) -> None:
    """Los parámetros de muestreo llegan al pipeline."""
    pipeline = async_client._pipeline_mock  # type: ignore[attr-defined]
    pipeline.responder_openai.reset_mock()
    await async_client.post(
        "/api/qa",
        json={
            "pregunta": "Hola",
            "temperatura": 0.7,
            "top_p": 0.95,
        },
    )
    pipeline.responder_openai.assert_called_once()
    _, kwargs = pipeline.responder_openai.call_args
    assert kwargs["temperatura"] == 0.7
    assert kwargs["top_p"] == 0.95
