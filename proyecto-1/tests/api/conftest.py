"""Fixtures para los tests del API FastAPI."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import crear_app
from tests.stream_mock_agente_m2 import astream_eventos_agente_minimos


@pytest_asyncio.fixture
async def async_client():
    """Cliente HTTP asincrónico con ASGI transport (sin red real)."""
    app = crear_app()
    grafo = MagicMock()

    grafo.astream_events = MagicMock(
        side_effect=lambda *a, **k: astream_eventos_agente_minimos(*a, **k)
    )
    app.state.grafo_agente = grafo
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client._grafo_mock = grafo  # type: ignore[attr-defined]
        yield client
