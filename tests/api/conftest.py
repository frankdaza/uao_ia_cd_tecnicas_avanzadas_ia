"""Fixtures para los tests del API FastAPI."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import crear_app


@pytest_asyncio.fixture
async def async_client():
    """Cliente HTTP asincrónico con ASGI transport (sin red real)."""
    app = crear_app()
    grafo = MagicMock()

    async def _stream_vacio(*_a: object, **_k: object):
        if False:
            yield {}

    grafo.astream_events = MagicMock(side_effect=lambda *a, **k: _stream_vacio())
    app.state.grafo_agente = grafo
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client._grafo_mock = grafo  # type: ignore[attr-defined]
        yield client
