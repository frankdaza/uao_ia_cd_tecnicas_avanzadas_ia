"""Tests del endpoint GET /api/modelos."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_modelos_estructura(async_client: AsyncClient) -> None:
    """GET /api/modelos devuelve listas de modelos y openai_disponible."""
    response = await async_client.get("/api/modelos")
    assert response.status_code == 200
    data = response.json()
    assert "modelos_ollama" in data
    assert "modelos_openai" in data
    assert "openai_disponible" in data
    assert isinstance(data["modelos_ollama"], list)
    assert isinstance(data["modelos_openai"], list)
    assert isinstance(data["openai_disponible"], bool)


@pytest.mark.asyncio
async def test_modelos_ollama_no_vacio(async_client: AsyncClient) -> None:
    """La lista de modelos Ollama tiene al menos un elemento."""
    response = await async_client.get("/api/modelos")
    data = response.json()
    assert len(data["modelos_ollama"]) > 0


@pytest.mark.asyncio
async def test_modelos_openai_sin_clave(async_client: AsyncClient) -> None:
    """Sin API key OpenAI configurada, openai_disponible es False."""
    response = await async_client.get("/api/modelos")
    data = response.json()
    assert data["openai_disponible"] is False
