"""Middleware de request-id y cabeceras de respuesta."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import crear_app


@pytest.mark.asyncio
async def test_responde_con_x_request_id() -> None:
    app = crear_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/salud")
        assert r.status_code == 200
        rid = r.headers.get("x-request-id")
        assert rid is not None
        assert len(rid) > 8


@pytest.mark.asyncio
async def test_reusa_x_request_id_del_cliente() -> None:
    app = crear_app()
    esperado = "mi-id-fijo-demo"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/salud", headers={"X-Request-ID": esperado})
        assert r.headers.get("x-request-id") == esperado
