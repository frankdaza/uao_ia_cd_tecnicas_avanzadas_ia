"""Tests del endpoint POST /api/qa (sincrónico)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from src.qa.cliente_ollama import OllamaNoAccesibleError


@pytest.mark.asyncio
async def test_qa_solo_ollama(async_client: AsyncClient) -> None:
    """POST /api/qa con Ollama activo retorna texto_ollama y fuentes."""
    response = await async_client.post(
        "/api/qa",
        json={
            "pregunta": "¿Cuáles son los servicios de urgencias?",
            "usar_ollama": True,
            "usar_openai": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["texto_ollama"] is not None
    assert data["texto_openai"] is None
    assert isinstance(data["fuentes"], list)
    assert data["metadatos_ollama"] is not None
    assert data["metadatos_openai"] is None


@pytest.mark.asyncio
async def test_qa_pregunta_vacia_rechazada(async_client: AsyncClient) -> None:
    """Una pregunta vacía devuelve 422 (validación Pydantic)."""
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "", "usar_ollama": True, "usar_openai": False},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_qa_sin_motor_activo(async_client: AsyncClient) -> None:
    """Sin motores activos retorna 400 con mensaje descriptivo."""
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Qué es la FVL?", "usar_ollama": False, "usar_openai": False},
    )
    assert response.status_code == 400
    assert "motor" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_qa_ollama_caido(async_client: AsyncClient) -> None:
    """Si Ollama no está accesible retorna 503 sin traceback."""
    async_client._pipeline_mock.responder.side_effect = OllamaNoAccesibleError(  # type: ignore[attr-defined]
        "http://localhost:11434"
    )
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Qué es la FVL?", "usar_ollama": True, "usar_openai": False},
    )
    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert "traceback" not in str(body).lower()


@pytest.mark.asyncio
async def test_qa_fuentes_en_respuesta(async_client: AsyncClient) -> None:
    """La respuesta incluye fuentes BM25 con los campos requeridos."""
    response = await async_client.post(
        "/api/qa",
        json={"pregunta": "¿Cuál es la misión de la FVL?", "usar_ollama": True, "usar_openai": False},
    )
    assert response.status_code == 200
    data = response.json()
    if data["fuentes"]:
        fuente = data["fuentes"][0]
        assert "archivo" in fuente
        assert "score" in fuente
        assert "source_url" in fuente
