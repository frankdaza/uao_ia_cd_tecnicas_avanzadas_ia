"""Tests del endpoint GET /api/salud."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_salud_retorna_ok(async_client: AsyncClient) -> None:
    """El health-check devuelve estado ok y versión."""
    response = await async_client.get("/api/salud")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_salud_content_type(async_client: AsyncClient) -> None:
    """El health-check devuelve JSON."""
    response = await async_client.get("/api/salud")
    assert "application/json" in response.headers["content-type"]
